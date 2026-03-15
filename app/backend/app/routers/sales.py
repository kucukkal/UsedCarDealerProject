import random
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
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


def validate_sales_rep_pricing(inv: models.Inventory, new_sale_price: float, is_sales_rep: bool):
    """
    SalesRep:
      - Can discount up to 10% from current inventory sale price
      - Profit must remain >= 20%
    Admin/Finance:
      - No 10% limit but profit must remain >= 5%
    """
    if new_sale_price <= 0:
        raise HTTPException(status_code=400, detail="Sale price must be greater than 0.")

    profit_percent = compute_profit_percent(inv.cost, new_sale_price)

    if is_sales_rep:
        min_allowed_price = inv.sale_price * 0.90
        if new_sale_price < min_allowed_price:
            raise HTTPException(status_code=400, detail="SalesRep cannot discount more than 10%.")
        if profit_percent < 20.0:
            raise HTTPException(status_code=400, detail="Profit must remain at least 20% for SalesRep.")
    else:
        if profit_percent < 5.0:
            raise HTTPException(status_code=400, detail="Profit below minimum threshold (5%).")


def random_interest_for_score(credit_band: str) -> float:
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
        raise HTTPException(status_code=400, detail="Invalid credit score band.")
    return round(random.uniform(low, high), 2)


def compute_monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    if term_months <= 0:
        return 0.0

    if annual_rate <= 0:
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
    Returns the monthly_payment value to store on Sale.
    """

    monthly_payment: Optional[float] = sale.monthly_payment if sale else None

    if not payload.status:
        raise HTTPException(status_code=400, detail="Status is required.")
    if not payload.payment_method:
        raise HTTPException(status_code=400, detail="Payment method is required.")

    if sale is not None:
        allowed = {
            "Under Contract": {"Under Contract", "Under Writing", "Sold"},
            "Under Writing": {"Under Writing", "Sold"},
            "Sold": {"Sold"},
        }
        prev_status = sale.status
        if prev_status in allowed and payload.status not in allowed[prev_status]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status change from {prev_status} to {payload.status}.",
            )

    # New loan deals must start in Under Contract
    if sale is None and payload.payment_method == "Loan" and payload.status != "Under Contract":
        raise HTTPException(status_code=400, detail="Loan deals must start in Under Contract status.")

    def ensure_min_deposit():
        if payload.deposit is None:
            raise HTTPException(status_code=400, detail="Deposit is required.")
        if payload.deposit < 0.05 * payload.sale_price:
            raise HTTPException(status_code=400, detail="Deposit must be at least 5% of sale price.")

    # Under Contract
    if payload.status == "Under Contract":
        if payload.payment_method == "Loan":
            ensure_min_deposit()
            if not payload.credit_score:
                raise HTTPException(status_code=400, detail="Credit score band is required for Loan.")
            if payload.term_months is None:
                raise HTTPException(status_code=400, detail="Loan term (months) is required for Loan.")
            if payload.interest_rate is None:
                payload.interest_rate = random_interest_for_score(payload.credit_score)
        else:
            ensure_min_deposit()
        return monthly_payment

    # Under Writing
    if payload.status == "Under Writing":
        if payload.payment_method == "Loan":
            if payload.deposit is not None and payload.deposit < 0.05 * payload.sale_price:
                raise HTTPException(status_code=400, detail="Deposit must be at least 5% of sale price.")

            if payload.term_months is not None and not (12 <= payload.term_months <= 48):
                raise HTTPException(status_code=400, detail="Loan term must be between 12 and 48 months.")

            if payload.credit_score and payload.interest_rate is None:
                payload.interest_rate = random_interest_for_score(payload.credit_score)

            if payload.interest_rate is not None and payload.term_months is not None:
                principal = payload.sale_price - (payload.deposit or 0.0)
                monthly_payment = compute_monthly_payment(
                    principal=principal,
                    annual_rate=payload.interest_rate,
                    term_months=payload.term_months,
                )
        else:
            payload.deposit = None
            payload.interest_rate = None
            payload.credit_score = None
            payload.term_months = None
            monthly_payment = None
        return monthly_payment

    # Sold
    if payload.status == "Sold":
        if payload.payment_method == "Loan":
            ensure_min_deposit()
            if not payload.credit_score:
                raise HTTPException(status_code=400, detail="Credit score band is required for Loan.")
            if payload.term_months is None:
                raise HTTPException(status_code=400, detail="Loan term (months) is required for Loan.")
            if payload.interest_rate is None:
                payload.interest_rate = random_interest_for_score(payload.credit_score)

            principal = payload.sale_price - payload.deposit
            monthly_payment = compute_monthly_payment(
                principal=principal,
                annual_rate=payload.interest_rate,
                term_months=payload.term_months,
            )
        else:
            payload.deposit = None
            payload.interest_rate = None
            payload.credit_score = None
            payload.term_months = None
            monthly_payment = None

        return monthly_payment

    return monthly_payment


def free_under_writing_cars(db: Session):
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
        inv = db.query(models.Inventory).filter(models.Inventory.vin_number == sale.vin_number).first()
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
    # IMPORTANT: sold cars are hidden in inventory, not deleted
    query = db.query(models.Inventory).filter(models.Inventory.status.notin_(["Sold"]))

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
            sub_model=inv.sub_model,
            vehicle_type=inv.vehicle_type,
            color=inv.color,
            antique=inv.antique,
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
    current_user: models.User = Depends(require_roles("Admin", "Finance", "SalesRep")),
):
    # 1) Find inventory car
    inv = db.query(models.Inventory).filter(models.Inventory.vin_number == payload.vin_number).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Car not found in inventory.")

    if not is_privileged(current_user) and current_user.role == "SalesRep":
        if inv.location != current_user.location:
            raise HTTPException(status_code=403, detail="Not enough permissions for this location.")

    # 2) Pricing rules
    is_sales_rep = current_user.role == "SalesRep"
    validate_sales_rep_pricing(inv, payload.sale_price, is_sales_rep)

    # 3) Find existing active sale (non-sold)
    sale = (
        db.query(models.Sale)
        .filter(models.Sale.vin_number == payload.vin_number, models.Sale.status != "Sold")
        .first()
    )

    # 4) Loan/status rules
    monthly_payment = apply_status_specific_rules(payload, inv, sale)
    now = datetime.now()

    # 5) Create or update Sale row
    if sale is None:
        temp_sale = models.Sale(
            sale_id="",
            vin_number=payload.vin_number,
            sale_price=payload.sale_price,
            status=payload.status,
            payment_method=payload.payment_method,
            deposit=payload.deposit,
            interest_rate=payload.interest_rate,
            credit_score=payload.credit_score,
            term_months=payload.term_months,
            monthly_payment=monthly_payment,

            # NEW customer fields
            customer_name=payload.customer_name,
            customer_zipcode=payload.customer_zipcode,
            customer_city=payload.customer_city,
            customer_state=payload.customer_state,
            customer_phone=payload.customer_phone,

            created_at=now,
            updated_at=now,
            status_under_contract_at=now if payload.status == "Under Contract" else None,
            status_under_writing_at=now if payload.status == "Under Writing" else None,
            status_sold_at=now if payload.status == "Sold" else None,
        )
        db.add(temp_sale)
        db.flush()

        temp_sale.sale_id = f"{now.month:02d}{now.day:02d}{now.year}{temp_sale.id}"
        sale = temp_sale
    else:
        sale.sale_price = payload.sale_price
        sale.status = payload.status
        sale.payment_method = payload.payment_method
        sale.deposit = payload.deposit
        sale.interest_rate = payload.interest_rate
        sale.credit_score = payload.credit_score
        sale.term_months = payload.term_months
        sale.monthly_payment = monthly_payment

        # NEW customer fields (always updated)
        sale.customer_name = payload.customer_name
        sale.customer_zipcode = payload.customer_zipcode
        sale.customer_city = payload.customer_city
        sale.customer_state = payload.customer_state
        sale.customer_phone = payload.customer_phone

        sale.updated_at = now

        if payload.status == "Under Contract" and sale.status_under_contract_at is None:
            sale.status_under_contract_at = now
        elif payload.status == "Under Writing" and sale.status_under_writing_at is None:
            sale.status_under_writing_at = now
        elif payload.status == "Sold" and sale.status_sold_at is None:
            sale.status_sold_at = now

    # 6) Inventory handling (per your final rule):
    #    - Sold should NOT remove car; just hide it by marking status Sold.
    #    - Under Writing should also hide it from other pages.
    if payload.status == "Under Writing":
        inv.status = "Under Writing"
    elif payload.status == "Sold":
        inv.status = "Sold"

        # Create a customer snapshot row for this SOLD deal
        # (One row per sale_id)
        existing = db.query(models.Customer).filter(models.Customer.sale_id == sale.sale_id).first()
        if existing is None:
            customer_row = models.Customer(
                customer_name=payload.customer_name,
                customer_zipcode=payload.customer_zipcode,
                customer_city=payload.customer_city,
                customer_state=payload.customer_state,
                customer_phone=payload.customer_phone,
                sale_id=sale.sale_id,
                vin_number=inv.vin_number,
                make=inv.make,
                model=inv.model,
                sub_model=inv.sub_model,
                year=inv.year,
                mileage=inv.mileage,
                vehicle_type=inv.vehicle_type,
                color=inv.color,
                antique=inv.antique,
                condition_type=inv.condition_type,
                sale_price=payload.sale_price,
                location=inv.location,
                created_at=now,
            )
            db.add(customer_row)

    db.commit()
    db.refresh(sale)
    return schemas.SaleRead.from_orm(sale)
