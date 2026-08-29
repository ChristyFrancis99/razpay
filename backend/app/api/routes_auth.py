from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.database.database import get_db
from app.database.models import User

router = APIRouter(prefix="/api/auth", tags=["authentication"])
VALID_ROLES = {"INVESTIGATOR", "MANAGER", "ADMINISTRATOR"}


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(..., min_length=8, max_length=256)
    role: str = "INVESTIGATOR"


def _ensure_bootstrap_admin(db: Session) -> None:
    if db.query(User).count() == 0 and settings.DEFAULT_ADMIN_PASSWORD:
        db.add(User(username=settings.DEFAULT_ADMIN_USERNAME, password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD), role="ADMINISTRATOR", is_active=1))
        db.commit()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    _ensure_bootstrap_admin(db)
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user.id, user.username, user.role)
    return LoginResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_TTL_SECONDS, user={"id": user.id, "username": user.username, "role": user.role})


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": int(user["sub"]), "username": user["username"], "role": user["role"]}


@router.post("/users", status_code=201)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if current.get("role") != "ADMINISTRATOR":
        raise HTTPException(status_code=403, detail="Only administrators can create users")
    role = payload.role.upper()
    if role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {sorted(VALID_ROLES)}")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=role, is_active=1)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role, "is_active": bool(user.is_active)}
