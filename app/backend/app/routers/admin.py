from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from app.database import get_db
from app.routers.auth import require_roles
from app import models

router = APIRouter(prefix="/admin", tags=["admin"])

def is_reset_allowed() -> bool:
    return os.getenv("ALLOW_DB_RESET", "false").lower() == "true"


@router.post("/reset-db")
def reset_database(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin")),
):
    if not is_reset_allowed():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Database reset is disabled on this environment.",
        )

    # ⚠️ Adjust table names to match your actual DB schema
    db.execute(
        text(
            """
            TRUNCATE TABLE finance, sales, service, audit_log, inventory, users
            RESTART IDENTITY CASCADE;
            """
        )
    )
    db.commit()

    return {"detail": "Database reset successfully (tables truncated)."}
