"""Groups API: CRUD for groups and group membership."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.models import Group, GroupMember, User
from app.db.session import get_session

logger = structlog.get_logger()
router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    """Request body for creating a group."""

    name: str
    member_emails: list[str] = []


class AddMemberRequest(BaseModel):
    """Request body for adding a member by email."""

    email: str


class UpdateSplitsRequest(BaseModel):
    """Request body for updating split percentages."""

    splits: dict[str, float]


class MemberResponse(BaseModel):
    """A group member with user details."""

    id: str
    user_id: str
    email: str
    name: str
    default_split_percent: float


class GroupResponse(BaseModel):
    """Full group detail with member list."""

    id: str
    name: str
    created_by: str
    members: list[MemberResponse]
    created_at: str


class GroupListItem(BaseModel):
    """Summary item for group listing."""

    id: str
    name: str
    member_count: int
    created_at: str


def _build_group_response(group: Group, session: Session) -> GroupResponse:
    """Build a GroupResponse with full member details."""
    members_db = session.exec(
        select(GroupMember).where(GroupMember.group_id == group.id)
    ).all()

    members = []
    for gm in members_db:
        user = session.get(User, gm.user_id)
        if user:
            members.append(MemberResponse(
                id=str(gm.id),
                user_id=str(user.id),
                email=user.email,
                name=user.name,
                default_split_percent=gm.default_split_percent,
            ))

    return GroupResponse(
        id=str(group.id),
        name=group.name,
        created_by=str(group.created_by),
        members=members,
        created_at=group.created_at.isoformat(),
    )


@router.get("", response_model=list[GroupListItem])
def list_groups(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[GroupListItem]:
    """List all groups the current user belongs to."""
    memberships = session.exec(
        select(GroupMember).where(GroupMember.user_id == user.id)
    ).all()
    group_ids = [m.group_id for m in memberships]

    if not group_ids:
        return []

    groups = session.exec(select(Group).where(Group.id.in_(group_ids))).all()  # type: ignore[attr-defined]
    result = []
    for g in groups:
        member_count = len(
            session.exec(select(GroupMember).where(GroupMember.group_id == g.id)).all()
        )
        result.append(GroupListItem(
            id=str(g.id),
            name=g.name,
            member_count=member_count,
            created_at=g.created_at.isoformat(),
        ))
    return result


@router.post("", response_model=GroupResponse)
def create_group(
    body: CreateGroupRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> GroupResponse:
    """Create a new group and add the creator as a member."""
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Group name is required")

    group = Group(name=body.name.strip(), created_by=user.id)
    session.add(group)
    session.flush()

    all_member_users = [user]
    for email in body.member_emails:
        member_user = session.exec(select(User).where(User.email == email)).first()
        if member_user and member_user.id != user.id:
            all_member_users.append(member_user)

    split_pct = round(100.0 / len(all_member_users), 2) if all_member_users else 100.0
    for u in all_member_users:
        gm = GroupMember(
            group_id=group.id,
            user_id=u.id,
            default_split_percent=split_pct,
        )
        session.add(gm)

    session.commit()
    session.refresh(group)

    logger.info("group_created", group_id=str(group.id), name=group.name, member_count=len(all_member_users))
    return _build_group_response(group, session)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> GroupResponse:
    """Get a group by ID."""
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

    return _build_group_response(group, session)


@router.post("/{group_id}/members", response_model=GroupResponse)
def add_member(
    group_id: UUID,
    body: AddMemberRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> GroupResponse:
    """Add a member to a group by email."""
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

    new_user = session.exec(select(User).where(User.email == body.email)).first()
    if not new_user:
        raise HTTPException(status_code=404, detail="User not found — they must register first")

    existing = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == new_user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member")

    existing_members = session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id)
    ).all()
    new_count = len(existing_members) + 1
    equal_pct = round(100.0 / new_count, 2)

    for m in existing_members:
        m.default_split_percent = equal_pct
        session.add(m)

    gm = GroupMember(group_id=group_id, user_id=new_user.id, default_split_percent=equal_pct)
    session.add(gm)

    session.commit()
    session.refresh(group)

    logger.info("member_added", group_id=str(group_id), user_email=body.email)
    return _build_group_response(group, session)


@router.put("/{group_id}/splits", response_model=GroupResponse)
def update_splits(
    group_id: UUID,
    body: UpdateSplitsRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> GroupResponse:
    """Update default split percentages for a group."""
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

    total = sum(body.splits.values())
    if abs(total - 100.0) > 0.1:
        raise HTTPException(status_code=400, detail=f"Splits must sum to 100% (got {total}%)")

    for user_id_str, pct in body.splits.items():
        gm = session.exec(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == UUID(user_id_str),
            )
        ).first()
        if gm:
            gm.default_split_percent = pct
            session.add(gm)

    session.commit()
    session.refresh(group)
    return _build_group_response(group, session)
