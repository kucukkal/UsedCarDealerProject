from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    location = Column(String, nullable=False)


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    vin_number = Column(String, unique=True, index=True, nullable=False)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    mileage = Column(Integer, nullable=False)
    condition_type = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    profit_percent = Column(Float, nullable=False)
    status = Column(String, default="available")
    location = Column(String, nullable=False)
    pr_update_count = Column(Integer, default=0)
    sales = relationship("Sale", back_populates="inventory")


# app/models.py
class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(String, unique=True, index=True)

    vin_number = Column(String, ForeignKey("inventory.vin_number"), nullable=False)

    sale_price = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # 'Under Contract', 'Under Writing', 'Sold'
    payment_method = Column(String, nullable=False)  # 'Cash', 'Credit', 'Loan'

    # Loan-related fields
    deposit = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    credit_score = Column(String, nullable=True)
    term_months = Column(Integer, nullable=True)
    monthly_payment = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    status_under_contract_at = Column(DateTime, nullable=True)
    status_under_writing_at = Column(DateTime, nullable=True)
    status_sold_at = Column(DateTime, nullable=True)

    inventory = relationship("Inventory", back_populates="sales")


class Service(Base):
    __tablename__ = "service"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, unique=True, index=True, nullable=False)
    vin_number = Column(String, ForeignKey("inventory.vin_number"))
    seriousness_level = Column(String, nullable=False)  # High, Medium, Low
    estimated_days = Column(Integer, nullable=False)
    cost_added = Column(Float, default=0)
    status = Column(String, default="In Service")
    created_at = Column(DateTime, default=datetime.utcnow)


# backend/app/models.py


class Finance(Base):
    __tablename__ = "finance"

    id = Column(Integer, primary_key=True, index=True)

    # Business ID for finance record (F000001 / I000001, etc.)
    finance_id = Column(String, unique=True, index=True, nullable=False)

    # Link back to sale / inventory
    sale_id = Column(String, nullable=True)
    vin_number = Column(String, index=True, nullable=False)

    # Cost comes from Inventory
    cost = Column(Float, nullable=False, default=0.0)

    sale_price = Column(Float, nullable=False, default=0.0)
    status = Column(String, nullable=False, default="Available")  # Sold / Available / In Service / etc.

    payment_type = Column(String, nullable=True)  # Cash / Credit / Loan / None (for pure inventory)
    deposit = Column(Float, nullable=False, default=0.0)
    loan_term = Column(Integer, nullable=True)
    loan_interest = Column(Float, nullable=True)
    monthly_payment = Column(Float, nullable=True)

    cc_fee = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    final_sale_price = Column(Float, nullable=False, default=0.0)

    amount_paid = Column(Float, nullable=False, default=0.0)
    amount_remaining = Column(Float, nullable=False, default=0.0)

    net_profit = Column(Float, nullable=False, default=0.0)
    profit_now = Column(Float, nullable=False, default=0.0)

    # Date when the sale became Sold (if applicable)
    sale_date = Column(Date, nullable=True)

    # Optional timestamps if you want them
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class AuditLog(Base):
    __tablename__ = "audit_log"
    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    record_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)
