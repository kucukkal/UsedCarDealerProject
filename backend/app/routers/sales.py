# backend/app/routers/sales.py
import random
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app import models, schemas
from app.routers.auth import require_roles, is_privileged

router = APIRouter(tags=["sales"])

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def compute_profit_percent(cost: float, sale_price: float) -> float:
    if cost <= 0:
        return 0.0
    return ((sale_price - cost) / cost) * 100.0


def validate_sales_rep_pricing(
    inv: models.Inventory,
    new_sale_price: float,
    is_sales_rep: bool,
):
    """
    SalesRep rule:
      - Can discount up to 10% from current inventory sale price
      - Profit must remain >= 20%
    Admin/Finance:
      - No 10% limit but profit must remain >= 5%
    """
    if new_sale_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale price must be greater than 0.",
        )

    profit_percent = compute_profit_percent(inv.cost, new_sale_price)

    if is_sales_rep:
        min_allowed_price = inv.sale_price * 0.90  # max 10% discount
        if new_sale_price < min_allowed_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SalesRep cannot discount more than 10%.",
            )
        if profit_percent < 20.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profit must remain at least 20% for SalesRep.",
            )
    else:
        if profit_percent < 5.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profit below minimum threshold (5%).",
            )


# Credit score label → interest range
CREDIT_SCORE_BRACKETS = {
    "Excellent": (0.0, 0.9),
    "Very Good": (1.0, 2.0),
    "Good": (2.0, 5.0),
    "Average": (5.0, 7.0),
    "Poor": (7.0, 10.0),
}


def random_interest_for_score(credit_band: str) -> float:
    """
    Choose a random interest rate based on credit score band.
    credit_band is one of: Excellent, Very Good, Good, Average, Poor.
    """
    band = (credit_band or "").strip().lower()
    if band == "excellent":
        low, high = 0.0, 0.9
    elif band == "very good":
        low, high = 1.0, 2.0
    elif band == "good":
        low, high = 2.0, 5.0
    elif band == "average":
        low, high = 5.0, 7.0
    elif band == "poor":
        low, high = 7.0, 10.0
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credit score band.",
        )

    return round(random.uniform(low, high), 2)


def compute_monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    """
    Standard amortization formula.
    annual_rate is percent (e.g., 5.0 for 5%)
    """
    if annual_rate <= 0:
        # zero-interest case
        return round(principal / term_months, 2)

    monthly_rate = (annual_rate / 100) / 12
    payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** (-term_months))

    return round(payment, 2)

def apply_status_specific_rules(
    payload: schemas.SaleCreateOrUpdate,
    inv: models.Inventory,
    sale: Optional[models.Sale],
) -> Optional[float]:
    """
    Enforce status/payment/loan rules and compute monthly_payment when needed.

    Returns:
        monthly_payment (float or None) to be stored on the Sale row.
        (We do NOT write monthly_payment into the Pydantic payload.)
    """

    monthly_payment: Optional[float] = sale.monthly_payment if sale else None

    # 1) Status & payment method required
    if not payload.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required.",
        )
    if not payload.payment_method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment method is required.",
        )

    # 2) Enforce allowed status transitions if sale already exists
    if sale is not None:
        allowed = {
            "Under Contract": {"Under Contract", "Under Writing", "Sold"},
            "Under Writing": {"Under Writing", "Sold"},
            "Sold": {"Sold"},
        }
        prev_status = sale.status
        if prev_status in allowed and payload.status not in allowed[prev_status]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status change from {prev_status} to {payload.status}.",
            )

    # 3) If payment is Loan and this is a NEW sale, must start at Under Contract
    if sale is None and payload.payment_method == "Loan" and payload.status != "Under Contract":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loan deals must start in Under Contract status.",
        )

    # Helper: ensure deposit >= 5% of sale_price
    def ensure_min_deposit():
        if payload.deposit is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deposit is required.",
            )
        if payload.deposit < 0.05 * payload.sale_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deposit must be at least 5% of sale price.",
            )

    # ---------- Under Contract ----------
    if payload.status == "Under Contract":
        if payload.payment_method == "Loan":
            # Deposit, credit score band, term are mandatory
            ensure_min_deposit()
            if not payload.credit_score:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credit score band is required for Loan.",
                )
            if payload.term_months is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Loan term (months) is required for Loan.",
                )

            # Fill interest_rate if missing
            if payload.interest_rate is None:
                payload.interest_rate = random_interest_for_score(payload.credit_score)
        else:
            # Cash / Credit but still enforce min deposit rule per your spec
            ensure_min_deposit()

        # No monthly payment yet in Under Contract
        return monthly_payment

    # ---------- Under Writing ----------
    if payload.status == "Under Writing":
        if payload.payment_method == "Loan":
            # Deposit & term optional here, but if provided must obey rules
            if payload.deposit is not None and payload.deposit < 0.05 * payload.sale_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Deposit must be at least 5% of sale price.",
                )

            if payload.term_months is not None and not (12 <= payload.term_months <= 48):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Loan term must be between 12 and 48 months.",
                )

            if payload.credit_score and payload.interest_rate is None:
                payload.interest_rate = random_interest_for_score(payload.credit_score)

            # Compute monthly payment if we now have rate & term
            if payload.interest_rate is not None and payload.term_months is not None:
                principal = payload.sale_price - (payload.deposit or 0.0)
                monthly_payment = compute_monthly_payment(
                    principal=principal,
                    annual_rate=payload.interest_rate,
                    months=payload.term_months,
                )
        else:
            # Cash / Credit: clear loan-related fields
            payload.deposit = None
            payload.interest_rate = None
            payload.credit_score = None
            payload.term_months = None
            monthly_payment = None

        return monthly_payment

    # ---------- Sold ----------
    if payload.status == "Sold":
        if payload.payment_method == "Loan":
            # All loan fields must be present & valid
            ensure_min_deposit()
            if not payload.credit_score:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credit score band is required for Loan.",
                )
            if payload.term_months is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Loan term (months) is required for Loan.",
                )
            if payload.interest_rate is None:
                payload.interest_rate = random_interest_for_score(payload.credit_score)

            principal = payload.sale_price - payload.deposit
            monthly_payment = compute_monthly_payment(
                principal=principal,
                annual_rate=payload.interest_rate,
                months=payload.term_months,
            )
        else:
            # Cash / Credit: loan-related fields must be blank
            payload.deposit = None
            payload.interest_rate = None
            payload.credit_score = None
            payload.term_months = None
            monthly_payment = None

        return monthly_payment

    # For any other status (if ever added), just keep existing monthly_payment
    return monthly_payment

def free_under_writing_cars(db: Session):
    """
    Cron helper: at 9 AM daily, free cars stuck in Under Writing more than 3 days.

    - Restore car to Inventory (status 'Available')
    - Delete the Sales record
    """
    cutoff = datetime.now() - timedelta(days=3)

    stuck_sales = (
        db.query(models.Sale)
        .filter(
            models.Sale.status == "Under Writing",
            models.Sale.status_under_writing_at != None,  # noqa: E711
            models.Sale.status_under_writing_at < cutoff,
        )
        .all()
    )

    for sale in stuck_sales:
        # Restore the car to Inventory if still present
        inv = (
            db.query(models.Inventory)
            .filter(models.Inventory.vin_number == sale.vin_number)
            .first()
        )
        if inv:
            inv.status = "Available"
        db.delete(sale)

    db.commit()

# -------------------------------------------------
# Endpoints
# -------------------------------------------------


@router.get("/", response_model=List[schemas.SaleListItem])
def list_sales(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "SalesRep")),
):
    """
    List sales records.
    - Admin/Finance see all locations.
    - SalesRep sees only sales for cars in their location.
    """
    query = (
        db.query(models.Sale, models.Inventory.location)
        .join(models.Inventory, models.Sale.vin_number == models.Inventory.vin_number)
    )

    if not is_privileged(current_user) and current_user.role == "SalesRep":
        query = query.filter(models.Inventory.location == current_user.location)

    rows = query.all()
    results: List[schemas.SaleListItem] = []

    for sale, location in rows:
        results.append(
            schemas.SaleListItem(
                sale_id=sale.sale_id,
                vin_number=sale.vin_number,
                sale_price=sale.sale_price,
                status=sale.status,
                payment_method=sale.payment_method,
                deposit=sale.deposit,
                interest_rate=sale.interest_rate,
                credit_score=sale.credit_score,
                term_months=sale.term_months,
                monthly_payment=sale.monthly_payment,
                location=location,
            )
        )

    return results


@router.get("/inventory-search", response_model=List[schemas.SaleInventorySearchItem])
def search_inventory_for_sales(
    vin: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    condition_type: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    mileage_min: Optional[int] = None,
    mileage_max: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "SalesRep")),
):
    """
    Search inventory for cars that can be added to Sales.

    Filters:
      - VIN, Make, Model, Condition
      - year_min / year_max
      - mileage_min / mileage_max
      - price_min / price_max

    Rules:
      - If both min and max are provided: include values in [min, max].
      - If only min is provided: value >= min.
      - If only max is provided: value <= max.
    """
    query = db.query(models.Inventory).filter(
        models.Inventory.status.notin_(["Sold"])  # avoid already sold
    )

    # restrict location for SalesRep
    if not is_privileged(current_user) and current_user.role == "SalesRep":
        query = query.filter(models.Inventory.location == current_user.location)

    if vin:
        query = query.filter(models.Inventory.vin_number.ilike(f"%{vin}%"))
    if make:
        query = query.filter(models.Inventory.make.ilike(f"%{make}%"))
    if model:
        query = query.filter(models.Inventory.model.ilike(f"%{model}%"))
    if condition_type:
        query = query.filter(models.Inventory.condition_type.ilike(f"%{condition_type}%"))

    if year_min is not None:
        query = query.filter(models.Inventory.year >= year_min)
    if year_max is not None:
        query = query.filter(models.Inventory.year <= year_max)

    if mileage_min is not None:
        query = query.filter(models.Inventory.mileage >= mileage_min)
    if mileage_max is not None:
        query = query.filter(models.Inventory.mileage <= mileage_max)

    if price_min is not None:
        query = query.filter(models.Inventory.sale_price >= price_min)
    if price_max is not None:
        query = query.filter(models.Inventory.sale_price <= price_max)

    cars = query.order_by(models.Inventory.year.desc()).all()

    return [
        schemas.SaleInventorySearchItem(
            vin_number=inv.vin_number,
            make=inv.make,
            model=inv.model,
            year=inv.year,
            mileage=inv.mileage,
            condition_type=inv.condition_type,
            sale_price=inv.sale_price,
            cost=inv.cost,
            location=inv.location,
            status=inv.status,
        )
        for inv in cars
    ]

@router.post("/", response_model=schemas.SaleRead)
def create_or_update_sale(
    payload: schemas.SaleCreateOrUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("Admin", "Finance", "SalesRep")
    ),
):
    """
    Create a new sale or update an existing active sale for the given VIN.

    SalesRep:
      - can adjust sale price up to 10% discount from inventory sale_price
      - must keep profit >= 20%

    Admin / Finance:
      - no 10% limit but profit must remain >= 5%.

    Loan payments must provide loan-related fields depending on status rules.
    """
    # 1. Find inventory car by VIN
    inv = (
        db.query(models.Inventory)
        .filter(models.Inventory.vin_number == payload.vin_number)
        .first()
    )
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found in inventory.",
        )

    # Restrict location for SalesRep
    if not is_privileged(current_user) and current_user.role == "SalesRep":
        if inv.location != current_user.location:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions for this location.",
            )

    # 2. Validate pricing rules
    is_sales_rep = current_user.role == "SalesRep"
    validate_sales_rep_pricing(inv, payload.sale_price, is_sales_rep)

    # 3. Find existing sale (non-Sold) for this VIN, if any
    sale = (
        db.query(models.Sale)
        .filter(
            models.Sale.vin_number == payload.vin_number,
            models.Sale.status != "Sold",
        )
        .first()
    )

    # 4. Apply status-specific & loan rules, compute monthly_payment (if needed)
    monthly_payment = apply_status_specific_rules(payload, inv, sale)

    now = datetime.now()

    # 5. Create or update Sale row
    if sale is None:
        # create new sale record
        temp_sale = models.Sale(
            sale_id="",  # will fill after flush
            vin_number=payload.vin_number,
            sale_price=payload.sale_price,
            status=payload.status,
            payment_method=payload.payment_method,
            deposit=payload.deposit,
            interest_rate=payload.interest_rate,
            credit_score=payload.credit_score,
            term_months=payload.term_months,
            monthly_payment=monthly_payment,
            created_at=now,
            updated_at=now,
            status_under_contract_at=now if payload.status == "Under Contract" else None,
            status_under_writing_at=now if payload.status == "Under Writing" else None,
            status_sold_at=now if payload.status == "Sold" else None,
        )
        db.add(temp_sale)
        db.flush()  # get temp_sale.id

        sale_id = f"{now.month:02d}{now.day:02d}{now.year}{temp_sale.id}"
        temp_sale.sale_id = sale_id

        sale = temp_sale
    else:
        # update existing sale
        sale.sale_price = payload.sale_price
        sale.status = payload.status
        sale.payment_method = payload.payment_method
        sale.deposit = payload.deposit
        sale.interest_rate = payload.interest_rate
        sale.credit_score = payload.credit_score
        sale.term_months = payload.term_months
        sale.monthly_payment = monthly_payment
        sale.updated_at = now

        if payload.status == "Under Contract":
            if sale.status_under_contract_at is None:
                sale.status_under_contract_at = now
        elif payload.status == "Under Writing":
            if sale.status_under_writing_at is None:
                sale.status_under_writing_at = now
        elif payload.status == "Sold":
            if sale.status_sold_at is None:
                sale.status_sold_at = now

    # 6. Inventory handling:
    #    - Under Writing: hide car from other pages (status change) – you likely do this already.
    #    - Sold: DO NOT delete from Inventory anymore (Finance cron will handle it),
    #      just mark status = 'Sold'.
    if payload.status == "Under Writing":
        inv.status = "Under Writing"
    elif payload.status == "Sold":
        inv.status = "Sold"

    db.commit()
    db.refresh(sale)

    return schemas.SaleRead.from_orm(sale)


