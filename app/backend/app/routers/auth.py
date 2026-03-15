from datetime import datetime, timedelta
from typing import Optional
import os

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db
from app import models, schemas

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

router = APIRouter()


# ----------------------------
# Request models
# ----------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


# ----------------------------
# Password helpers
# ----------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ----------------------------
# JWT helpers
# ----------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str, db: Session) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def require_roles(*allowed_roles: str):
    """
    Usage:
        current_user: models.User = Depends(require_roles("Admin"))
    """
    def dependency(token: str = Depends(oauth2_bearer_token), db: Session = Depends(get_db)):
        current_user = get_current_user(token, db)
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return dependency


def is_privileged(user: models.User) -> bool:
    return user.role in ("Admin", "Finance")


# ----------------------------
# Bearer token extractor
# ----------------------------

from fastapi.security import OAuth2PasswordBearer
oauth2_bearer_token = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ----------------------------
# Auth endpoints
# ----------------------------

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Accepts JSON:
    {
      "username": "admin",
      "password": "admin123!"
    }
    """
    user = db.query(models.User).filter(models.User.username == payload.username).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        {
            "sub": user.username,
            "role": user.role,
            "location": user.location,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/seed-admin", response_model=schemas.User)
def seed_admin_user(db: Session = Depends(get_db)):
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_role = os.getenv("ADMIN_ROLE")
    admin_location = os.getenv("ADMIN_LOCATION")

    if not admin_username or not admin_password or not admin_role or not admin_location:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin environment variables are not configured."
        )

    existing = db.query(models.User).filter(models.User.username == admin_username).first()
    if existing:
        return existing

    admin = models.User(
        username=admin_username,
        password_hash=get_password_hash(admin_password),
        role=admin_role,
        location=admin_location,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


@router.post("/create-user", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin")),
):
    """
    Only Admin can create users.
    """
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        location=user.location,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user