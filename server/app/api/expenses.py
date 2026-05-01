"""Expenses API: create and list expenses within a group."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.models import Expense, ExpenseSplit, Group, GroupMember, User
from app.db.session import get_session

logger = structlog.get_logger()
router = APIRouter(prefix="/api/groups/{group_id}/expenses", tags=["expenses"])


class SplitInput(BaseModel):
    """A single split entry in an expense creation request."""

    user_id: str
    amount: float


class CreateExpenseRequest(BaseModel):
    """Request body for creating an expense."""

    description: str
    amount: float
    paid_by: str
    splits: list[SplitInput] | None = None


class SplitResponse(BaseModel):
    """A split entry in an expense response."""

    user_id: str
    user_name: str
    user_email: str
    amount: float


class ExpenseResponse(BaseModel):
    """An expense with its splits."""

    id: str
    description: str
    amount: float
    paid_by: str
    paid_by_name: str
    splits: list[SplitResponse]
    created_at: str


def _check_membership(
    group_id: UUID, user_id: UUID, session: Session,
) -> Group:
    """Verify group exists and user is a member."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    return group


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    group_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[ExpenseResponse]:
    """List expenses for a group, newest first."""
    _check_membership(group_id, user.id, session)

    expenses = session.exec(
        select(Expense)
        .where(Expense.group_id == group_id)
        .order_by(Expense.created_at.desc())  # type: ignore[union-attr]
    ).all()

    result = []
    for exp in expenses:
        payer = session.get(User, exp.paid_by)
        splits_db = session.exec(
            select(ExpenseSplit).where(ExpenseSplit.expense_id == exp.id)
        ).all()
        splits = []
        for s in splits_db:
            u = session.get(User, s.user_id)
            splits.append(SplitResponse(
                user_id=str(s.user_id),
                user_name=u.name if u else "",
                user_email=u.email if u else "",
                amount=s.amount,
            ))
        result.append(ExpenseResponse(
            id=str(exp.id),
            description=exp.description,
            amount=exp.amount,
            paid_by=str(exp.paid_by),
            paid_by_name=payer.name if payer else "",
            splits=splits,
            created_at=exp.created_at.isoformat(),
        ))
    return result


@router.post("", response_model=ExpenseResponse)
def create_expense(
    group_id: UUID,
    body: CreateExpenseRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ExpenseResponse:
    """Create a new expense in a group."""
    _check_membership(group_id, user.id, session)

    if not body.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    paid_by_uuid = UUID(body.paid_by)
    payer_membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == paid_by_uuid,
        )
    ).first()
    if not payer_membership:
        raise HTTPException(status_code=400, detail="Payer must be a group member")

    expense = Expense(
        group_id=group_id,
        description=body.description.strip(),
        amount=body.amount,
        paid_by=paid_by_uuid,
        created_by=user.id,
    )
    session.add(expense)
    session.flush()

    if body.splits:
        split_total = sum(s.amount for s in body.splits)
        if abs(split_total - body.amount) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Splits sum ({split_total}) must equal expense amount ({body.amount})",
            )
        for s in body.splits:
            es = ExpenseSplit(
                expense_id=expense.id,
                user_id=UUID(s.user_id),
                amount=s.amount,
            )
            session.add(es)
    else:
        members = session.exec(
            select(GroupMember).where(GroupMember.group_id == group_id)
        ).all()
        for m in members:
            split_amount = round(body.amount * m.default_split_percent / 100.0, 2)
            es = ExpenseSplit(
                expense_id=expense.id,
                user_id=m.user_id,
                amount=split_amount,
            )
            session.add(es)

    session.commit()
    session.refresh(expense)

    payer = session.get(User, expense.paid_by)
    splits_db = session.exec(
        select(ExpenseSplit).where(ExpenseSplit.expense_id == expense.id)
    ).all()
    splits = []
    for s in splits_db:
        u = session.get(User, s.user_id)
        splits.append(SplitResponse(
            user_id=str(s.user_id),
            user_name=u.name if u else "",
            user_email=u.email if u else "",
            amount=s.amount,
        ))

    logger.info(
        "expense_created",
        expense_id=str(expense.id),
        group_id=str(group_id),
        amount=body.amount,
        description=body.description,
    )

    return ExpenseResponse(
        id=str(expense.id),
        description=expense.description,
        amount=expense.amount,
        paid_by=str(expense.paid_by),
        paid_by_name=payer.name if payer else "",
        splits=splits,
        created_at=expense.created_at.isoformat(),
    )
