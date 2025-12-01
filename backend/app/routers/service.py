from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.routers.auth import require_roles, is_privileged

# No prefix here – main.py uses prefix="/service"
router = APIRouter(tags=["service"])


def default_cost_for_seriousness(level: str) -> float:
    """
    Default repair cost based on seriousness.
    High   -> 2000
    Medium -> 1200
    Low    -> 500
    """
    s = (level or "").lower()
    if s == "high":
        return 2000.0
    if s == "medium":
        return 1200.0
    if s == "low":
        return 500.0
    return 0.0


def complete_service_record(db: Session, svc: models.Service) -> schemas.ServiceWithCarInfo:
    """
    Core logic to move a car out of Service and back to Inventory:
    - Inventory.cost += Service.cost_added
    - Inventory.status = "Available"
    - Service.status = "Completed"
    """
    inv = (
        db.query(models.Inventory)
        .filter(models.Inventory.vin_number == svc.vin_number)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    # Apply repair cost
    inv.cost = (inv.cost or 0) + (svc.cost_added or 0)
    # Car is now back in stock
    inv.status = "Available"

    svc.status = "Completed"

    db.commit()
    db.refresh(inv)
    db.refresh(svc)

    return schemas.ServiceWithCarInfo(
        id=svc.id,
        service_id=svc.service_id,
        vin_number=svc.vin_number,
        seriousness_level=svc.seriousness_level,
        estimated_days=svc.estimated_days,
        cost_added=svc.cost_added,
        status=svc.status,
        created_at=svc.created_at,
        make=inv.make,
        model=inv.model,
        year=inv.year,
        mileage=inv.mileage,
        service_start_date=svc.created_at.date(),
    )


@router.get("/", response_model=List[schemas.ServiceWithCarInfo])
def list_service(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "ServiceRep")),
):
    """
    List service records plus basic car info (make, model, year, mileage).
    - Admin sees all locations.
    - ServiceRep sees only their own location.
    """
    query = (
        db.query(
            models.Service,
            models.Inventory.make,
            models.Inventory.model,
            models.Inventory.year,
            models.Inventory.mileage,
        )
        .join(models.Inventory, models.Service.vin_number == models.Inventory.vin_number)
    )

    if not is_privileged(current_user):
        query = query.filter(models.Inventory.location == current_user.location)

    rows = query.all()
    results: list[schemas.ServiceWithCarInfo] = []

    for svc, make, model, year, mileage in rows:
        results.append(
            schemas.ServiceWithCarInfo(
                id=svc.id,
                service_id=svc.service_id,
                vin_number=svc.vin_number,
                seriousness_level=svc.seriousness_level,
                estimated_days=svc.estimated_days,
                cost_added=svc.cost_added,
                status=svc.status,
                created_at=svc.created_at,
                make=make,
                model=model,
                year=year,
                mileage=mileage,
                # Expose date-only for UI as Service Start Date
                service_start_date=svc.created_at.date(),
            )
        )

    return results


@router.post("/", response_model=schemas.ServiceRead)
def create_service(
    service: schemas.ServiceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "ServiceRep")),
):
    """
    Generic create (not used by UI normally). If you use it directly,
    you should provide cost_added explicitly.
    """
    db_service = models.Service(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


@router.patch("/{service_id}", response_model=schemas.ServiceWithCarInfo)
def update_service(
    service_id: str,
    update: schemas.ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("ServiceRep")),
):
    """
    Update service record fields that are managed from the Service page:
    - seriousness_level
    - estimated_days
    - service_start_date (entry date)
    - cost_added (repair cost)

    Rule:
    - If seriousness changes AND repair cost is not truly changed,
      auto-recalculate cost_added based on seriousness.
    - If repair cost is changed, use that updated value.
    """
    svc = (
        db.query(models.Service)
        .filter(models.Service.service_id == service_id)
        .first()
    )
    if not svc:
        raise HTTPException(status_code=404, detail="Service record not found")

    # Check location restriction for ServiceRep
    inv = (
        db.query(models.Inventory)
        .filter(models.Inventory.vin_number == svc.vin_number)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    if not is_privileged(current_user) and inv.location != current_user.location:
        raise HTTPException(
            status_code=403, detail="Not enough permissions for this location"
        )

    data = update.dict(exclude_unset=True)

    # Capture old values so we can detect real changes
    old_seriousness = svc.seriousness_level
    old_cost = svc.cost_added

    # Get new seriousness from payload (if provided)
    new_seriousness = data.get("seriousness_level", old_seriousness)
    seriousness_changed = (
        "seriousness_level" in data and new_seriousness != old_seriousness
    )

    # Apply updates

    if "seriousness_level" in data and data["seriousness_level"] is not None:
        svc.seriousness_level = data["seriousness_level"]

    if "estimated_days" in data and data["estimated_days"] is not None:
        svc.estimated_days = data["estimated_days"]

    if "service_start_date" in data and data["service_start_date"] is not None:
        d = data["service_start_date"]
        svc.created_at = datetime(d.year, d.month, d.day, 0, 0, 0)

    # cost_added logic:
    #  - if cost_added is present and DIFFERENT from old value -> treat as explicit edit
    #  - if seriousness changed and cost_added not changed (or not present)
    #    -> recalc from seriousness
    explicit_cost = data.get("cost_added", None)
    has_cost_in_payload = "cost_added" in data and explicit_cost is not None

    if has_cost_in_payload:
        # If the user sent a new value and it's different from old, use it
        if explicit_cost != old_cost:
            svc.cost_added = explicit_cost
        else:
            # Same cost, but if seriousness changed, recompute
            if seriousness_changed:
                svc.cost_added = default_cost_for_seriousness(new_seriousness)
    else:
        # No cost in payload; if seriousness changed, recompute automatically
        if seriousness_changed:
            svc.cost_added = default_cost_for_seriousness(new_seriousness)

    db.commit()
    db.refresh(svc)

    # Rebuild joined response
    result = (
        db.query(
            models.Service,
            models.Inventory.make,
            models.Inventory.model,
            models.Inventory.year,
            models.Inventory.mileage,
        )
        .join(models.Inventory, models.Service.vin_number == models.Inventory.vin_number)
        .filter(models.Service.id == svc.id)
        .first()
    )
    svc2, make, model, year, mileage = result

    return schemas.ServiceWithCarInfo(
        id=svc2.id,
        service_id=svc2.service_id,
        vin_number=svc2.vin_number,
        seriousness_level=svc2.seriousness_level,
        estimated_days=svc2.estimated_days,
        cost_added=svc2.cost_added,
        status=svc2.status,
        created_at=svc2.created_at,
        make=make,
        model=model,
        year=year,
        mileage=mileage,
        service_start_date=svc2.created_at.date(),
    )


@router.post("/simple-entry", response_model=schemas.ServiceWithCarInfo)
def simple_service_entry(
    payload: schemas.ServiceSimpleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("ServiceRep")),
):
    """
    Quick service entry used from Service page.

    Required:
      - vin_number
      - seriousness_level (High/Medium/Low)

    Optional:
      - estimated_days (if not provided, default based on seriousness)
      - cost_added (if not provided, auto-calculated by seriousness)

    Also:
      - marks inventory.status = "In Service"
    """
    # Find car in inventory
    inv = (
        db.query(models.Inventory)
        .filter(models.Inventory.vin_number == payload.vin_number)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Car not found in inventory")

    # Location restriction for ServiceRep
    if not is_privileged(current_user) and inv.location != current_user.location:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for this location",
        )

    # Avoid duplicate "In Service" record
    existing = (
        db.query(models.Service)
        .filter(
            models.Service.vin_number == payload.vin_number,
            models.Service.status == "In Service",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This car is already in service (status In Service).",
        )

    now = datetime.now()

    # Simple service_id: MMDDYYYY + sequence (use inventory id to keep unique)
    service_id = f"{now.month:02d}{now.day:02d}{now.year}{inv.id}"

    # Default estimated_days based on seriousness if not provided
    days = payload.estimated_days
    if days is None:
        seriousness = payload.seriousness_level.lower()
        if seriousness == "high":
            days = 3
        elif seriousness == "medium":
            days = 2
        else:
            days = 1

    # 🔹 Default repair cost if not provided
    cost_added = payload.cost_added
    if cost_added is None:
        cost_added = default_cost_for_seriousness(payload.seriousness_level)

    svc = models.Service(
        service_id=service_id,
        vin_number=payload.vin_number,
        seriousness_level=payload.seriousness_level,
        estimated_days=days,
        cost_added=cost_added,
        status="In Service",
    )
    db.add(svc)

    # Mark inventory item as in service
    inv.status = "In Service"

    db.commit()
    db.refresh(svc)

    # Build response with car info
    return schemas.ServiceWithCarInfo(
        id=svc.id,
        service_id=svc.service_id,
        vin_number=svc.vin_number,
        seriousness_level=svc.seriousness_level,
        estimated_days=svc.estimated_days,
        cost_added=svc.cost_added,
        status=svc.status,
        created_at=svc.created_at,
        make=inv.make,
        model=inv.model,
        year=inv.year,
        mileage=inv.mileage,
        service_start_date=svc.created_at.date(),
    )


@router.post("/{service_id}/complete", response_model=schemas.ServiceWithCarInfo)
def complete_service_endpoint(
    service_id: str,
    db: Session = Depends(get_db),
    # 🔒 Only ServiceRep can manually complete
    current_user: models.User = Depends(require_roles("ServiceRep")),
):
    """
    Manually complete a service record from the Service page.
    - Only ServiceRep can call this.
    - Uses same logic as nightly cron: inventory cost updated, car becomes available.
    """
    svc = (
        db.query(models.Service)
        .filter(
            models.Service.service_id == service_id,
            models.Service.status == "In Service",
        )
        .first()
    )
    if not svc:
        raise HTTPException(
            status_code=404, detail="In-service record not found for this ID"
        )

    # Location restriction
    inv = (
        db.query(models.Inventory)
        .filter(models.Inventory.vin_number == svc.vin_number)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    if not is_privileged(current_user) and inv.location != current_user.location:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for this location",
        )

    return complete_service_record(db, svc)
