"""Authentication: JWT tokens, password hashing, and FastAPI dependencies."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
import structlog
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.config import settings
from app.db.models import User
from app.db.session import get_session

logger = structlog.get_logger()

_bearer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET_KEY: str = ""
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_jwt(user_id: UUID, email: str, name: str) -> str:
    """Create a JWT token for the given user."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def init_auth() -> str:
    """Initialise the JWT secret key. Called during app startup."""
    global JWT_SECRET_KEY
    key = settings.fairshare_secret_key
    if not key:
        key = secrets.token_urlsafe(32)
        logger.warning("no_secret_key_set", msg="Auto-generated secret key")

    JWT_SECRET_KEY = settings.jwt_secret if settings.jwt_secret else key
    return key


def ensure_admin_user(session: Session) -> User:
    """Get or create the admin user."""
    from sqlmodel import select

    admin = session.exec(select(User).where(User.email == "admin@fairshare.local")).first()
    if admin:
        return admin

    secret_key = settings.fairshare_secret_key or "admin"
    admin = User(
        email="admin@fairshare.local",
        password_hash=hash_password(secret_key),
        name="Admin",
        is_admin=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    logger.info("admin_user_created", email=admin.email)
    return admin


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    """FastAPI dependency that returns the authenticated user."""
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt(creds.credentials)
        user_id = UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
