"""Payments API: record and list manual payments within a group."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.models import Group, GroupMember, Payment, User
from app.db.session import get_session
from app.limiter import limiter

logger = structlog.get_logger()
router = APIRouter(prefix="/api/groups/{group_id}/payments", tags=["payments"])


class CreatePaymentRequest(BaseModel):
    """Request body for recording a payment."""

    to_user_id: str = Field(..., max_length=36)
    amount: float = Field(..., gt=0, le=1_000_000)
    note: str = Field("", max_length=200)


class PaymentResponse(BaseModel):
    """A payment record in the response."""

    id: str
    from_user_id: str
    from_name: str
    to_user_id: str
    to_name: str
    amount: float
    note: str
    created_at: str


def _build_response(pmt: Payment, session: Session) -> PaymentResponse:
    """Build a PaymentResponse from a Payment model."""
    from_u = session.get(User, pmt.from_user)
    to_u = session.get(User, pmt.to_user)
    return PaymentResponse(
        id=str(pmt.id),
        from_user_id=str(pmt.from_user),
        from_name=from_u.name if from_u else "",
        to_user_id=str(pmt.to_user),
        to_name=to_u.name if to_u else "",
        amount=pmt.amount,
        note=pmt.note,
        created_at=pmt.created_at.isoformat(),
    )


@router.get("", response_model=list[PaymentResponse])
@limiter.limit("60/minute")
def list_payments(
    group_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[PaymentResponse]:
    """List all payments in a group, newest first."""
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

    payments = session.exec(
        select(Payment)
        .where(Payment.group_id == group_id)
        .order_by(Payment.created_at.desc())  # type: ignore[union-attr]
    ).all()

    return [_build_response(p, session) for p in payments]


@router.post("", response_model=PaymentResponse)
@limiter.limit("20/minute")
def create_payment(
    group_id: UUID,
    request: Request,
    body: CreatePaymentRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PaymentResponse:
    """Record a manual payment between two group members."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    from_membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user.id,
        )
    ).first()
    if not from_membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    to_uuid = UUID(body.to_user_id)
    if to_uuid == user.id:
        raise HTTPException(status_code=400, detail="Cannot pay yourself")

    to_membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == to_uuid,
        )
    ).first()
    if not to_membership:
        raise HTTPException(status_code=400, detail="Recipient is not a group member")

    pmt = Payment(
        group_id=group_id,
        from_user=user.id,
        to_user=to_uuid,
        amount=body.amount,
        note=body.note,
        created_by=user.id,
    )
    session.add(pmt)
    session.commit()
    session.refresh(pmt)

    logger.info(
        "payment_created",
        payment_id=str(pmt.id),
        group_id=str(group_id),
        from_user=str(user.id),
        to_user=str(to_uuid),
        amount=body.amount,
    )

    return _build_response(pmt, session)
