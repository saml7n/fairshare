"""Balances API: net balances and graph-minimised simplified debts."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from parbaked import current_user as get_current_user
from models import Expense, ExpenseSplit, Group, GroupMember, Payment
from parbaked.auth.models import User
from parbaked import get_session
from services import compute_net_balances, minimise_transfers

logger = structlog.get_logger()
router = APIRouter()


class MemberBalance(BaseModel):
    """Net balance for a single group member."""

    user_id: str
    name: str
    email: str
    balance: float


class SimplifiedDebt(BaseModel):
    """A single optimised transfer between two members."""

    from_user_id: str
    from_name: str
    to_user_id: str
    to_name: str
    amount: float


class BalancesResponse(BaseModel):
    """Full balances response for a group."""

    balances: list[MemberBalance]
    simplified_debts: list[SimplifiedDebt]



@router.get("", response_model=BalancesResponse)
def get_balances(
    group_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> BalancesResponse:
    """Get net balances and simplified debts for a group."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id)
    ).all()
    expenses = session.exec(
        select(Expense).where(Expense.group_id == group_id)
    ).all()
    expense_ids = [e.id for e in expenses]

    splits: list[ExpenseSplit] = []
    if expense_ids:
        splits = list(session.exec(
            select(ExpenseSplit).where(ExpenseSplit.expense_id.in_(expense_ids))  # type: ignore[union-attr]
        ).all())

    payments = list(session.exec(
        select(Payment).where(Payment.group_id == group_id)
    ).all())

    net = compute_net_balances(expenses, splits, payments)

    user_cache: dict[UUID, User] = {}
    for m in members:
        if m.user_id not in user_cache:
            u = session.get(User, m.user_id)
            if u:
                user_cache[m.user_id] = u
        if m.user_id not in net:
            net[m.user_id] = 0.0

    balance_list = []
    for uid, bal in net.items():
        u = user_cache.get(uid)
        balance_list.append(MemberBalance(
            user_id=str(uid),
            name=u.name if u else "",
            email=u.email if u else "",
            balance=round(bal, 2),
        ))

    transfers = minimise_transfers(net)
    debts = []
    for from_id, to_id, amount in transfers:
        from_u = user_cache.get(from_id)
        to_u = user_cache.get(to_id)
        debts.append(SimplifiedDebt(
            from_user_id=str(from_id),
            from_name=from_u.name if from_u else "",
            to_user_id=str(to_id),
            to_name=to_u.name if to_u else "",
            amount=amount,
        ))

    logger.info(
        "balances_computed",
        group_id=str(group_id),
        member_count=len(members),
        debt_count=len(debts),
    )

    return BalancesResponse(balances=balance_list, simplified_debts=debts)
