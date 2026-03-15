# backend/app/main.py
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import SessionLocal, engine
from app import models
from app.routers import auth, inventory, sales, service, finance, promotion, admin
from app.routers.service import complete_service_record
from app.routers.sales import free_under_writing_cars
from app.routers.finance import build_finance_snapshot

load_dotenv()


# ------------------ NIGHTLY SERVICE COMPLETION (21:00) ------------------ #
# main.py (add near the top)
# add this import


def run_daily_finance_snapshot():
    """
    Called once per day at ~09:00 (9 AM).
    Rebuilds the Finance snapshot from Sales + Inventory.
    """
    db = SessionLocal()
    try:
        build_finance_snapshot(db)
    finally:
        db.close()


async def finance_scheduler_task():
    """
    Async background task that sleeps until the next 09:00,
    runs the finance snapshot job, then repeats.
    """
    while True:
        now = datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        run_daily_finance_snapshot()

def run_nightly_service_completion():
    """
    Called once per day at ~21:00 (9 PM).
    - Finds all Service records In Service whose (start_date + estimated_days) <= today.
    - Completes them: updates Inventory cost & status.
    """
    db = SessionLocal()
    try:
        today = datetime.now().date()

        svc_list = (
            db.query(models.Service)
            .filter(models.Service.status == "In Service")
            .all()
        )

        for svc in svc_list:
            start_date = svc.created_at.date()
            # If estimated_days passed (or today is after that)
            if start_date + timedelta(days=svc.estimated_days) <= today:
                complete_service_record(db, svc)
    finally:
        db.close()


async def nightly_scheduler_task():
    """
    Async background task that sleeps until the next 21:00,
    runs the nightly completion job, then repeats.
    """
    while True:
        now = datetime.now()
        target = now.replace(hour=21, minute=0, second=0, microsecond=0)
        if target <= now:
            # If it's already past 21:00, schedule for tomorrow 21:00
            target += timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        run_nightly_service_completion()


# ------------------ MORNING SALES CLEANUP (09:00) ------------------ #

def run_morning_sales_cleanup():
    """
    Called once per day at ~09:00 (9 AM).
    - Finds cars in Sales with status='Under Writing' older than 3 days.
    - Restores them to Inventory and removes Sales records.
    """
    db = SessionLocal()
    try:
        free_under_writing_cars(db)
    finally:
        db.close()


async def morning_scheduler_task():
    """
    Async background task that sleeps until the next 09:00,
    runs the Under Writing cleanup job, then repeats.
    """
    while True:
        now = datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if target <= now:
            # If it's already past 09:00, schedule for tomorrow 09:00
            target += timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        run_morning_sales_cleanup()


# ------------------ FASTAPI LIFESPAN ------------------ #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context:
    - On startup: start nightly scheduler
    - On startup: start Finance 9AM snapshot scheduler
    """
    # Existing nightly service completion job (21:00 or your modified time)
    asyncio.create_task(nightly_scheduler_task())

    # NEW — daily 9 AM Finance snapshot job
    asyncio.create_task(finance_scheduler_task())

    yield
    # If you ever want to cancel tasks / cleanup, do it here.


print("Creating database tables (if not exist)...")
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Used Car Dealer API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(sales.router, prefix="/sales", tags=["sales"])
app.include_router(service.router, prefix="/service", tags=["service"])
app.include_router(finance.router, prefix="/finance", tags=["finance"])
app.include_router(promotion.router, prefix="/promotion", tags=["promotion"])
app.include_router(admin.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
