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


# ---------------------------------------------------------------------------
# Expense + ExpenseSplit (Story 4)
# ---------------------------------------------------------------------------

class Expense(SQLModel, table=True):
    """An expense recorded in a group."""

    __tablename__ = "expenses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id")
    description: str = Field(default="")
    amount: float = Field(default=0.0)
    paid_by: UUID = Field(foreign_key="users.id")
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=_utcnow)


class ExpenseSplit(SQLModel, table=True):
    """How an expense is split among group members."""

    __tablename__ = "expense_splits"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    expense_id: UUID = Field(foreign_key="expenses.id")
    user_id: UUID = Field(foreign_key="users.id")
    amount: float = Field(default=0.0)


# ---------------------------------------------------------------------------
# Payment (Story 6 model, created here for Story 5 balance calculations)
# ---------------------------------------------------------------------------

class Payment(SQLModel, table=True):
    """A manual payment from one user to another within a group."""

    __tablename__ = "payments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id")
    from_user: UUID = Field(foreign_key="users.id")
    to_user: UUID = Field(foreign_key="users.id")
    amount: float = Field(default=0.0)
    note: str = Field(default="")
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=_utcnow)
