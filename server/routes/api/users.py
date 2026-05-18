"""Users API: search for users to add to groups."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from parbaked import current_user as get_current_user
from parbaked.auth.models import User
from parbaked import get_session

logger = structlog.get_logger()
router = APIRouter()


class UserSearchResult(BaseModel):
    """A user returned from search."""

    id: str
    email: str
    name: str


@router.get("/search", response_model=list[UserSearchResult])
def search_users(
    q: str = Query(..., min_length=2, max_length=100),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[UserSearchResult]:
    """Search users by exact email match. Excludes the current user."""
    query = q.strip().lower()
    if "@" not in query:
        return []

    match = session.exec(
        select(User).where(User.id != user.id, User.email == query)
    ).first()
    if not match:
        return []

    return [UserSearchResult(id=str(match.id), email=match.email, name=match.name)]
