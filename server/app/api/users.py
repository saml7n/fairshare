"""Users API: search for users to add to groups."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.models import User
from app.db.session import get_session

logger = structlog.get_logger()
router = APIRouter(prefix="/api/users", tags=["users"])


class UserSearchResult(BaseModel):
    """A user returned from search."""

    id: str
    email: str
    name: str


@router.get("/search", response_model=list[UserSearchResult])
def search_users(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[UserSearchResult]:
    """Search users by email or name prefix."""
    query = q.lower()
    users = session.exec(select(User)).all()
    results = []
    for u in users:
        if u.id == user.id:
            continue
        if query in u.email.lower() or query in u.name.lower():
            results.append(UserSearchResult(
                id=str(u.id),
                email=u.email,
                name=u.name,
            ))
    return results[:20]
