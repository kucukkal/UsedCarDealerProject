# app/routers/promotion.py

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.routers.auth import require_roles, is_privileged

router = APIRouter( tags=["promotion"])


# ---------- Pydantic Schemas for PR Updates ----------

class PRPriceUpdate(BaseModel):
    vin_number: str
    sale_price: Optional[float] = None
    discount_percent: Optional[float] = None
    raise_percent: Optional[float] = None

    @field_validator("sale_price", "discount_percent", "raise_percent")
    @classmethod
    def non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("Values must be non-negative")
        return v

    @field_validator("discount_percent", "raise_percent")
    @classmethod
    def max_ten_percent(cls, v):
        # We still validate in endpoint, but this keeps absurd input out
        if v is not None and v > 100:
            raise ValueError("Percent values must be reasonable (≤100)")
        return v

    @property
    def filled_fields_count(self) -> int:
        count = 0
        if self.sale_price is not None:
            count += 1
        if self.discount_percent is not None:
            count += 1
        if self.raise_percent is not None:
            count += 1
        return count


# ---------- GET /promotion/inventory ----------

@router.get("/inventory")
def get_promotion_inventory(
    include_service: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "PR")),
):
    """
    Returns inventory grouped by location for PR/ Admin.

    Response shape:
    {
      "Denver": [ {car1}, {car2}, ... ],
      "New York": [ ... ],
      ...
    }

    Rules:
    - Exclude cars with status in ["Under Contract", "Sold"].
    - By default, exclude cars whose status == "In Service",
      unless include_service=true (then they are included but remain uneditable).
    """

    query = db.query(models.Inventory)

    # Always hide sold/under contract cars from PR pricing view
    query = query.filter(~models.Inventory.status.in_(["Under Contract", "Sold"]))

    if not include_service:
        query = query.filter(models.Inventory.status != "In Service")

    # Admin can see all locations; PR sees all locations for VIEW,
    # but update endpoint will enforce location limitations.
    cars = query.all()

    grouped: Dict[str, List[dict]] = {}

    for car in cars:
        loc = car.location or "Unknown"
        if loc not in grouped:
            grouped[loc] = []

        grouped[loc].append(
            {
                "vin_number": car.vin_number,
                "make": car.make,
                "model": car.model,
                "year": car.year,
                "mileage": car.mileage,
                "condition_type": car.condition_type,
                "cost": float(car.cost),
                "sale_price": float(car.sale_price),
                "status": car.status,
                "location": car.location,
                # If you added PR update count / last update info to your model,
                # you can expose it here as well.
                # "pr_update_count": getattr(car, "pr_update_count", 0),
            }
        )

    return grouped


# ---------- POST /promotion/update-price ----------

@router.post("/update-price")
def update_promotion_price(
    payload: PRPriceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "PR")),
):
    """
    PR / Admin price update logic.

    Fields:
      - vin_number (required)
      - Exactly ONE of: sale_price, discount_percent, raise_percent

    Constraints:
      - PR:
          * max 10% price change per update (up/down)
          * final profit >= 20%
          * max 2 successful updates per car (requires pr_update_count column
            on Inventory, default 0)
          * can only update cars in their own location
      - Admin:
          * can change any car in any location
          * must keep profit >= 5%
          * not limited by 10% or per-car update count
    """

    # Validate exactly one of sale_price/discount_percent/raise_percent
    if payload.filled_fields_count != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one of sale_price, discount_percent, or raise_percent must be provided.",
        )

    # Fetch inventory item
    car = (
        db.query(models.Inventory)
        .filter(models.Inventory.vin_number == payload.vin_number)
        .first()
    )
    if not car:
        raise HTTPException(status_code=404, detail="Car not found for given VIN")

    # Location restriction for PR
    if current_user.role == "PR":
        if car.location != current_user.location:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="VIN does not belong to your location.",
            )

    # Cannot modify cars that are in Service or in Sales pipeline
    if car.status in ["In Service", "Under Contract", "Under Writing", "Sold"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Car status does not allow PR price changes.",
        )

    old_price = float(car.sale_price)
    cost = float(car.cost)

    if cost <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cost for profit calculation.",
        )

    # Compute new_sale_price based on which field is filled
    if payload.sale_price is not None:
        new_price = float(payload.sale_price)
        if new_price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sale price must be positive.",
            )

        change_percent = ((new_price - old_price) * 100.0) / old_price

    elif payload.discount_percent is not None:
        disc = float(payload.discount_percent)
        if disc <= 0 or disc > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discount percent must be >0 and ≤10 for PR.",
            )
        new_price = old_price * (1 - disc / 100.0)
        change_percent = -disc  # negative means discount

    else:  # raise_percent
        raise_pct = float(payload.raise_percent)
        if raise_pct <= 0 or raise_pct > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Raise percent must be >0 and ≤10 for PR.",
            )
        new_price = old_price * (1 + raise_pct / 100.0)
        change_percent = raise_pct

    # Role-specific validation
    if current_user.role == "PR":
        # 1) Per-update ±10% limit
        if abs(change_percent) > 10.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price change exceeds allowed 10% limit.",
            )

        # 2) Per-car update limit (assumes Inventory.pr_update_count column):
        pr_update_count = getattr(car, "pr_update_count", 0)
        if pr_update_count >= 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PR has reached the maximum number of price updates for this car.",
            )

    # Profit checks
    new_profit_percent = ((new_price - cost) / cost) * 100.0

    if current_user.role == "PR":
        if new_profit_percent < 20.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profit margin cannot drop below 20%.",
            )
    else:  # Admin
        if new_profit_percent < 5.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profit below minimum threshold (5%).",
            )

    # All good → apply changes
    car.sale_price = new_price
    car.profit_percent = new_profit_percent

    # Increment PR counter if PR
    if current_user.role == "PR":
        if hasattr(car, "pr_update_count"):
            car.pr_update_count = (car.pr_update_count or 0) + 1

    db.commit()
    db.refresh(car)

    return {
        "detail": "Price updated successfully.",
        "vin_number": car.vin_number,
        "new_sale_price": car.sale_price,
        "new_profit_percent": car.profit_percent,
        # "pr_update_count": getattr(car, "pr_update_count", None),
    }
