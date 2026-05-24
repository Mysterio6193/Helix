"""Organization management service — members, invitations, usage."""
from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.billing import PLAN_FREE, get_plan_limits
from helix.models.brand import Brand
from helix.models.enterprise import ApiKey, OrganizationInvitation
from helix.models.organization import User, Workspace
from helix.models.workflow import WorkflowRun


def _generate_invite_token() -> str:
    return secrets.token_urlsafe(48)


async def create_invitation(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    invited_by: uuid.UUID,
    email: str,
    role: str = "member",
    expires_in_days: int = 7,
) -> OrganizationInvitation:
    token = _generate_invite_token()
    expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
    invitation = OrganizationInvitation(
        organization_id=organization_id,
        invited_by=invited_by,
        email=email,
        role=role,
        token=token,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.flush()
    await db.refresh(invitation)
    return invitation


async def accept_invitation(
    db: AsyncSession,
    *,
    token: str,
    user: User,
) -> OrganizationInvitation | None:
    q = select(OrganizationInvitation).where(
        OrganizationInvitation.token == token,
        OrganizationInvitation.accepted_at.is_(None),
        OrganizationInvitation.revoked_at.is_(None),
    )
    result = await db.execute(q)
    invitation = result.scalar_one_or_none()
    if not invitation:
        return None
    if invitation.expires_at.replace(tzinfo=None) < datetime.now(UTC).replace(tzinfo=None):
        return None
    if invitation.email != user.email:
        return None

    invitation.accepted_at = datetime.now(UTC).replace(tzinfo=None)
    user.organization_id = invitation.organization_id
    user.role = invitation.role
    await db.flush()
    await db.refresh(invitation)
    return invitation


async def list_invitations(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    include_accepted: bool = False,
) -> list[OrganizationInvitation]:
    q = select(OrganizationInvitation).where(
        OrganizationInvitation.organization_id == organization_id,
    )
    if not include_accepted:
        q = q.where(OrganizationInvitation.accepted_at.is_(None))
    q = q.order_by(OrganizationInvitation.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def revoke_invitation(db: AsyncSession, invitation: OrganizationInvitation) -> None:
    invitation.revoked_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()


async def list_members(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
) -> list[User]:
    q = select(User).where(
        User.organization_id == organization_id,
    ).order_by(User.created_at)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_member_role(
    db: AsyncSession,
    member: User,
    new_role: str,
) -> User:
    member.role = new_role
    await db.flush()
    await db.refresh(member)
    return member


async def remove_member(db: AsyncSession, member: User) -> None:
    await db.delete(member)
    await db.flush()


async def get_org_usage(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    plan: str = PLAN_FREE,
) -> dict:
    limits = get_plan_limits(plan)

    brand_count = (
        await db.execute(
            select(func.count())
            .select_from(Brand)
            .join(Workspace, Workspace.id == Brand.workspace_id)
            .where(Workspace.organization_id == organization_id)
        )
    ).scalar_one()

    now = datetime.now(UTC).replace(tzinfo=None)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    runs_this_month = (
        await db.execute(
            select(func.count())
            .select_from(WorkflowRun)
            .join(Brand, Brand.id == WorkflowRun.brand_id)
            .join(Workspace, Workspace.id == Brand.workspace_id)
            .where(
                Workspace.organization_id == organization_id,
                WorkflowRun.created_at >= month_start,
            )
        )
    ).scalar_one()

    member_count = (
        await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.organization_id == organization_id)
        )
    ).scalar_one()

    api_key_count = (
        await db.execute(
            select(func.count())
            .select_from(ApiKey)
            .where(ApiKey.organization_id == organization_id)
        )
    ).scalar_one()

    return {
        "brands": brand_count,
        "brand_limit": limits.get("brands", 1),
        "runs_this_month": runs_this_month,
        "run_limit": limits.get("runs_per_month", 50),
        "members": member_count,
        "member_limit": limits.get("members", 1),
        "api_keys": api_key_count,
        "api_key_limit": limits.get("api_keys", 5),
    }
