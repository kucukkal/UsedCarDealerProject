from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field


# --------------------
# User Schemas
# --------------------
class UserBase(BaseModel):
    username: str
    role: str
    location: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    user_id: int

    class Config:
        orm_mode = True


# =========================
# INVENTORY SCHEMAS
# =========================

class InventoryCreate(BaseModel):
    """
    Payload for creating a car from UI or Excel.

    Backend will:
    - generate vin_number (if None)
    - compute profit_percent
    - set status ("Available" or "In Service")
    """
    make: str
    model: str
    year: int
    mileage: int
    condition_type: str
    cost: float
    sale_price: float
    location: str
    # optional VIN: usually auto-generated
    vin_number: Optional[str] = None


class InventoryRead(BaseModel):
    """
    Shape of inventory rows returned to the frontend.
    """
    id: int
    vin_number: str
    make: str
    model: str
    year: int
    mileage: int
    condition_type: str
    cost: float
    sale_price: float
    profit_percent: Optional[float] = None
    status: str
    location: str

    class Config:
        orm_mode = True


class InventoryUpdate(BaseModel):
    """
    Partial update – all fields optional.
    Caller can change one or many properties at once.
    """
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    condition_type: Optional[str] = None
    cost: Optional[float] = None
    sale_price: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None
    # vin_number is not editable via UI, so omitted here


# =========================
# SALES SCHEMAS
# =========================

class SaleBase(BaseModel):
    vin_number: str
    sale_price: float
    status: str = Field(..., description="Under Writing, Under Contract, Sold")
    payment_method: str = Field(..., description="Cash, Credit, Loan")

    deposit: Optional[float] = None
    interest_rate: Optional[float] = None
    # credit_score is stored as a band label:
    #   Excellent, Very Good, Good, Average, Poor
    credit_score: Optional[str] = None
    term_months: Optional[int] = None
    # monthly_payment is NOT supplied by client; backend computes it


class SaleCreateOrUpdate(SaleBase):
    pass


class SaleRead(SaleBase):
    sale_id: str
    monthly_payment: Optional[float] = None

    created_at: datetime
    updated_at: datetime
    status_under_contract_at: Optional[datetime] = None
    status_under_writing_at: Optional[datetime] = None
    status_sold_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2 replacement for orm_mode


class SaleListItem(BaseModel):
    sale_id: str
    vin_number: str
    sale_price: float
    status: str
    payment_method: str
    deposit: Optional[float]
    interest_rate: Optional[float]
    credit_score: Optional[str]
    term_months: Optional[int]
    monthly_payment: Optional[float]
    location: str

    class Config:
        from_attributes = True


class SaleInventorySearchItem(BaseModel):
    vin_number: str
    make: str
    model: str
    year: int
    mileage: int
    condition_type: str
    sale_price: float
    cost: float
    location: str
    status: str

    class Config:
        from_attributes = True


# =========================
# SERVICE SCHEMAS
# =========================

class ServiceBase(BaseModel):
    service_id: str
    vin_number: str
    seriousness_level: str
    estimated_days: int
    cost_added: float = 0
    status: str = "In Service"


class ServiceCreate(ServiceBase):
    pass


class ServiceRead(ServiceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ServiceWithCarInfo(ServiceRead):
    make: str
    model: str
    year: int
    mileage: int
    # Date-only field for UI
    service_start_date: date


class ServiceUpdate(BaseModel):
    """
    Fields that can be edited from the Service page:
    - seriousness_level
    - estimated_days
    - service_start_date (entry date)
    """
    seriousness_level: Optional[str] = None
    estimated_days: Optional[int] = None
    service_start_date: Optional[date] = None
    cost_added: Optional[float] = None


class ServiceSimpleCreate(BaseModel):
    """
    Simple entry from Service page:
    - vin_number + seriousness_level (required)
    - estimated_days, cost_added (optional)
    """
    vin_number: str
    seriousness_level: str
    estimated_days: Optional[int] = None
    cost_added: Optional[float] = None


# =========================
# FINANCE SCHEMAS
# =========================

# --------------------
# Finance Schemas
# --------------------
from datetime import date

class FinanceBase(BaseModel):
    finance_id: str
    sale_id: Optional[str] = None
    vin_number: str

    # Cost comes from Inventory
    cost: float

    sale_price: float
    status: str

    payment_type: Optional[str] = None  # Cash / Credit / Loan / None for pure inventory
    deposit: Optional[float] = 0
    loan_term: Optional[int] = None
    loan_interest: Optional[float] = None
    monthly_payment: Optional[float] = None

    cc_fee: float = 0           # 5% of sale_price if Credit, else 0
    tax: float = 0              # 6% of sale_price
    final_sale_price: float = 0 # sale_price + tax

    amount_paid: float = 0      # for Loan
    amount_remaining: float = 0 # for Loan

    net_profit: float = 0       # final_sale_price - (cc_fee + tax + cost)
    profit_now: float = 0       # Cash/Credit: same as net_profit; Loan: amount_paid - cost

    sale_date: Optional[date] = None  # date when Status became Sold (if any)


class FinanceCreate(FinanceBase):
    pass


class FinanceRead(FinanceBase):
    id: int

    class Config:
        from_attributes = True
