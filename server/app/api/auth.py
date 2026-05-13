"""Auth API: register, login, and user info."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from app.auth import create_jwt, get_current_user, hash_password, verify_password
from app.config import settings
from app.db.models import User
from app.db.session import get_session
from app.limiter import limiter

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field("", max_length=100)
    invite_code: str = Field("", max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=128)


class AuthResponse(BaseModel):
    ok: bool
    token: str
    user: dict | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str


@router.post("/register", response_model=AuthResponse)
@limiter.limit("5/hour")
def register(request: Request, body: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    """Register a new user account."""
    expected = settings.registration_invite_code
    if not expected:
        raise HTTPException(status_code=403, detail="Registration is currently closed")
    if body.invite_code != expected:
        raise HTTPException(status_code=403, detail="Invalid invite code")

    normalized_email = body.email.strip().lower()
    existing = session.exec(select(User).where(User.email == normalized_email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = User(
        email=normalized_email,
        password_hash=hash_password(body.password),
        name=body.name.strip() or normalized_email.split("@")[0],
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
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    """Log in with email and password."""
    user = session.exec(select(User).where(User.email == body.email.strip().lower())).first()
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
