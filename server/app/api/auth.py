"""Auth API: register, login, and user info."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.auth import create_jwt, get_current_user, hash_password, verify_password
from app.db.models import User
from app.db.session import get_session

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    ok: bool
    token: str
    user: dict | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    """Register a new user account."""
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name or body.email.split("@")[0],
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_jwt(user.id, user.email, user.name)
    logger.info("user_registered", user_id=str(user.id), email=user.email)

    return AuthResponse(
        ok=True,
        token=token,
        user={"id": str(user.id), "email": user.email, "name": user.name},
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    """Log in with email and password."""
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_jwt(user.id, user.email, user.name)
    logger.info("user_logged_in", user_id=str(user.id), email=user.email)

    return AuthResponse(
        ok=True,
        token=token,
        user={"id": str(user.id), "email": user.email, "name": user.name},
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse(id=str(user.id), email=user.email, name=user.name)
