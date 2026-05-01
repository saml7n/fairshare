"""SQLModel database models for FairShare.

Models are added incrementally — one per story.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User (Story 2)
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    """A registered user account."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str = Field(default="")
    name: str = Field(default="")
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Group + GroupMember (Story 3)
# ---------------------------------------------------------------------------

class Group(SQLModel, table=True):
    """An expense group."""

    __tablename__ = "groups"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(default="")
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=_utcnow)


class GroupMember(SQLModel, table=True):
    """Membership linking a user to a group with a default split percentage."""

    __tablename__ = "group_members"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id")
    user_id: UUID = Field(foreign_key="users.id")
    default_split_percent: float = Field(default=0.0)
    joined_at: datetime = Field(default_factory=_utcnow)
