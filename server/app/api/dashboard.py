"""Dashboard API: cross-group balance summary for the current user."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.balances import compute_net_balances
from app.auth import get_current_user
from app.db.models import (
    Expense,
    ExpenseSplit,
    Group,
    GroupMember,
    Payment,
    User,
)
from app.db.session import get_session

logger = structlog.get_logger()
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class GroupSummary(BaseModel):
    """Balance summary for a single group."""

    group_id: str
    group_name: str
    balance: float
    member_count: int


class DashboardResponse(BaseModel):
    """Cross-group summary for the current user."""

    total_owed_to_you: float
    total_you_owe: float
    net_position: float
    groups: list[GroupSummary]


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DashboardResponse:
    """Get the current user's financial summary across all groups."""
    memberships = session.exec(
        select(GroupMember).where(GroupMember.user_id == user.id)
    ).all()

    groups: list[GroupSummary] = []
    total_owed_to_you = 0.0
    total_you_owe = 0.0

    for mem in memberships:
        group = session.get(Group, mem.group_id)
        if not group:
            continue

        members = session.exec(
            select(GroupMember).where(GroupMember.group_id == group.id)
        ).all()
        expenses = session.exec(
            select(Expense).where(Expense.group_id == group.id)
        ).all()
        expense_ids = [e.id for e in expenses]

        splits: list[ExpenseSplit] = []
        if expense_ids:
            splits = list(session.exec(
                select(ExpenseSplit).where(
                    ExpenseSplit.expense_id.in_(expense_ids)  # type: ignore[union-attr]
                )
            ).all())

        try:
            payments = list(session.exec(
                select(Payment).where(Payment.group_id == group.id)
            ).all())
        except Exception:
            payments = []

        net = compute_net_balances(expenses, splits, payments)
        my_balance = round(net.get(user.id, 0.0), 2)

        if my_balance > 0.01:
            total_owed_to_you += my_balance
        elif my_balance < -0.01:
            total_you_owe += abs(my_balance)

        groups.append(GroupSummary(
            group_id=str(group.id),
            group_name=group.name,
            balance=my_balance,
            member_count=len(members),
        ))

    net_position = round(total_owed_to_you - total_you_owe, 2)

    logger.info(
        "dashboard_computed",
        user_id=str(user.id),
        group_count=len(groups),
        net_position=net_position,
    )

    return DashboardResponse(
        total_owed_to_you=round(total_owed_to_you, 2),
        total_you_owe=round(total_you_owe, 2),
        net_position=net_position,
        groups=groups,
    )
