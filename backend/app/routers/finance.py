# backend/app/routers/finance.py
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.routers.auth import require_roles

router = APIRouter(tags=["finance"])


# ---------- Helpers ----------

def months_paid_since(
    sale_date: date,
    today: date,
    term_months: Optional[int],
) -> int:
    """
    Approximate number of loan installments paid, assuming:
    - Payments are due on the 10th of each month
    - A month is counted as paid if the 10th of that month has passed.
    """
    if term_months is None or term_months <= 0:
        return 0

    if sale_date > today:
        return 0

    # First due date: first 10th on or after sale_date
    if sale_date.day <= 10:
        first_due = sale_date.replace(day=10)
    else:
        # move to next month 10th
        if sale_date.month == 12:
            first_due = sale_date.replace(year=sale_date.year + 1, month=1, day=10)
        else:
            first_due = sale_date.replace(month=sale_date.month + 1, day=10)

    if today < first_due:
        return 0

    # Count whole months between first_due and today, including the current month if day >= 10
    months = (today.year - first_due.year) * 12 + (today.month - first_due.month)
    if today.day >= 10:
        months += 1

    if months < 0:
        months = 0

    # Do not exceed loan term
    return min(months, term_months)

def build_finance_snapshot(db: Session) -> None:
        """
        Rebuilds the finance table snapshot from Sales + Inventory tables.

        Rules:
          - Only status = 'Sold' from Sales produce full finance rows with taxes, payments, etc.
          - Sales with status != 'Sold' produce partial finance rows
            (only vin_number, cost, sale_price, status; everything else blank/zero).
          - Inventory rows (status != 'Sold') that have NO Sales row at all also produce partial rows.
          - We do NOT delete from Inventory here; we only read from it.
        """
        # Clear finance table completely before re-populating
        db.query(models.Finance).delete()
        db.flush()

        today = date.today()

        # ---- Step 1: process Sales ----
        sales_list: List[models.Sale] = db.query(models.Sale).all()

        for s in sales_list:
            # Try to find matching inventory for cost
            inv: Optional[models.Inventory] = (
                db.query(models.Inventory)
                .filter(models.Inventory.vin_number == s.vin_number)
                .first()
            )

            cost = inv.cost if inv else 0.0
            sale_date = s.status_sold_at.date() if s.status_sold_at else s.updated_at.date()

            payment_type = s.payment_method  # Cash / Credit / Loan
            status = s.status

            # Defaults
            cc_fee = 0.0
            tax = 0.0
            final_sale_price = 0.0
            amount_paid = 0.0
            amount_remaining = 0.0
            net_profit = 0.0
            profit_now = 0.0

            if status == "Sold":
                # --- FULL ROW FOR SOLD DEALS ---
                tax = round(s.sale_price * 0.06, 2)

                if payment_type == "Credit":
                    cc_fee = round(s.sale_price * 0.05, 2)

                # Final sale price = sale_price + tax
                final_sale_price = round(s.sale_price + tax, 2)

                if payment_type == "Loan" and s.term_months and s.monthly_payment:
                    # Calculate how many months have been paid up to today
                    m_paid = months_paid_since(sale_date, today, s.term_months)
                    amount_paid = round(m_paid * s.monthly_payment, 2)
                    amount_remaining = round(
                        max(0, s.term_months - m_paid) * s.monthly_payment, 2
                    )
                else:
                    amount_paid = 0.0
                    amount_remaining = 0.0

                net_profit = round(final_sale_price - (cc_fee + tax + cost), 2)

                if payment_type in ("Cash", "Credit"):
                    profit_now = net_profit
                elif payment_type == "Loan":
                    profit_now = round(amount_paid - cost, 2)
                else:
                    profit_now = 0.0

                deposit = s.deposit or 0.0
                loan_term = s.term_months
                loan_interest = s.interest_rate
                monthly_payment = s.monthly_payment

            else:
                # --- PARTIAL ROW FOR NON-SOLD DEALS ---
                # Only vin_number, cost, sale_price, status should carry meaning.
                # Everything else is blank / zero.
                payment_type = None
                deposit = 0.0
                loan_term = None
                loan_interest = None
                monthly_payment = None
                cc_fee = 0.0
                tax = 0.0
                final_sale_price = 0.0
                amount_paid = 0.0
                amount_remaining = 0.0
                net_profit = 0.0
                profit_now = 0.0
                sale_date = None

            finance_row = models.Finance(
                finance_id="",  # fill after flush
                sale_id=s.sale_id,
                vin_number=s.vin_number,
                cost=cost,
                sale_price=s.sale_price,
                status=status,
                payment_type=payment_type,
                deposit=deposit,
                loan_term=loan_term,
                loan_interest=loan_interest,
                monthly_payment=monthly_payment,
                cc_fee=cc_fee,
                tax=tax,
                final_sale_price=final_sale_price,
                amount_paid=amount_paid,
                amount_remaining=amount_remaining,
                net_profit=net_profit,
                profit_now=profit_now,
                sale_date=sale_date,
            )
            db.add(finance_row)
            db.flush()
            finance_row.finance_id = f"F{finance_row.id:06d}"

        db.flush()

        # ---- Step 2: add Inventory-only cars (no Sales row at all) ----
        sales_vins = {s.vin_number for s in sales_list}

        inv_list: List[models.Inventory] = (
            db.query(models.Inventory)
            .filter(models.Inventory.status != "Sold")
            .all()
        )

        for inv in inv_list:
            if inv.vin_number in sales_vins:
                # this car is already represented via Sales above
                continue

            finance_row = models.Finance(
                finance_id="",
                sale_id=None,
                vin_number=inv.vin_number,
                cost=inv.cost,
                sale_price=inv.sale_price,
                status=inv.status,  # Available / In Service
                payment_type=None,
                deposit=0.0,
                loan_term=None,
                loan_interest=None,
                monthly_payment=None,
                cc_fee=0.0,
                tax=0.0,
                final_sale_price=0.0,
                amount_paid=0.0,
                amount_remaining=0.0,
                net_profit=0.0,
                profit_now=0.0,
                sale_date=None,
            )
            db.add(finance_row)
            db.flush()
            finance_row.finance_id = f"I{finance_row.id:06d}"

        db.commit()

# ---------- Endpoints ----------

@router.get("/", response_model=List[schemas.FinanceRead])
def list_finance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "Finance")),
):
    """
    List all finance rows (snapshot).
    Finance user has access only to this page (enforced at router-level for other modules).
    """
    rows = db.query(models.Finance).order_by(models.Finance.id.desc()).all()
    return rows


@router.post("/run-daily-snapshot")
def run_daily_snapshot(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "Finance")),
):
    """
    Manually trigger the Finance snapshot job.
    This is also what your 9 AM cron job will call internally.
    """
    build_finance_snapshot(db)
    return {"detail": "Finance snapshot rebuilt successfully."}


@router.get("/summary")
def finance_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin", "Finance")),
):
    """
    Return high-level aggregated metrics for the Finance page:

      - total_assets:        Sum(cost) of all inventory cars (status != 'Sold').
      - projected_sale:      Sum(sale_price) of inventory cars (status != 'Sold').
      - projected_profit:    projected_sale - total_assets.
      - total_final_sold:    Sum(final_sale_price) for all rows whose status = 'Sold'.
      - total_tax_sold:      Sum(tax) for status = 'Sold'.
      - total_available_funds:
            For Cash/Credit: sum(final_sale_price)
            For Loan:        sum(amount_paid)
      - total_profit_now:
            total_available_funds - total cost of sold cars.
    """
    # Assets & projected from Inventory table directly
    inv_q = db.query(models.Inventory).filter(models.Inventory.status != "Sold")
    inv_rows: List[models.Inventory] = inv_q.all()

    total_assets = sum((inv.cost or 0.0) for inv in inv_rows)
    projected_sale = sum((inv.sale_price or 0.0) for inv in inv_rows)
    projected_profit = projected_sale - total_assets

    # Sold data from Finance snapshot
    fin_sold: List[models.Finance] = (
        db.query(models.Finance)
        .filter(models.Finance.status == "Sold")
        .all()
    )

    total_final_sold = sum((f.final_sale_price or 0.0) for f in fin_sold)
    total_tax_sold = sum((f.tax or 0.0) for f in fin_sold)

    # Available funds now
    total_available_funds = 0.0
    total_cost_sold = 0.0

    for f in fin_sold:
        total_cost_sold += (f.cost or 0.0)
        if f.payment_type in ("Cash", "Credit"):
            total_available_funds += (f.final_sale_price or 0.0)
        elif f.payment_type == "Loan":
            total_available_funds += (f.amount_paid or 0.0)

    total_profit_now = total_available_funds - total_cost_sold

    return {
        "total_assets": round(total_assets, 2),
        "projected_sale": round(projected_sale, 2),
        "projected_profit": round(projected_profit, 2),
        "total_final_sold": round(total_final_sold, 2),
        "total_tax_sold": round(total_tax_sold, 2),
        "total_available_funds": round(total_available_funds, 2),
        "total_profit_now": round(total_profit_now, 2),
    }
