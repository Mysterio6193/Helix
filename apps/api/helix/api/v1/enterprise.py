"""Enterprise API endpoints — API keys, audit logs, members, invitations, usage."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.billing import get_or_create_subscription
from helix.core.config import get_settings
from helix.core.db import get_db
from helix.core.rate_limiter import get_rate_limit_for_plan
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.schemas.common import Page
from helix.schemas.enterprise import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
    AuditLogRead,
    InvitationAccept,
    InvitationCreate,
    InvitationRead,
    MemberRead,
    MemberRoleUpdate,
    UsageRead,
)
from helix.services import api_keys as api_key_service
from helix.services import audit as audit_service
from helix.services import enterprise as enterprise_service
from helix.services import organization as org_service

router = APIRouter(prefix="", tags=["enterprise"])


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreated:
    """Create a new API key for programmatic access."""
    usage = await enterprise_service.get_org_usage(
        db, organization_id=user.organization_id
    )
    if usage["api_keys"] >= usage["api_key_limit"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API key limit reached for your plan",
        )

    key, raw = await api_key_service.create_api_key(db, payload, user=user)
    await db.commit()

    await audit_service.log_action(
        db, organization_id=user.organization_id, actor_id=user.id,
        action="api_key.create", resource_type="api_key", resource_id=str(key.id),
    )

    return ApiKeyCreated(
        id=key.id,
        organization_id=key.organization_id,
        user_id=key.user_id,
        name=key.name,
        key_prefix=key.key_prefix,
        scopes=key.scopes,
        expires_at=key.expires_at,
        last_used_at=key.last_used_at,
        enabled=key.enabled,
        created_at=key.created_at,
        updated_at=key.updated_at,
        raw_key=raw,
    )


@router.get("/api-keys", response_model=list[ApiKeyRead])
async def list_api_keys(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyRead]:
    """List all API keys for the user's organization."""
    keys = await api_key_service.list_api_keys(
        db, organization_id=user.organization_id, user_id=user.id
    )
    return [ApiKeyRead.model_validate(k) for k in keys]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Revoke an API key."""
    key = await api_key_service.get_api_key(db, key_id)
    if not key or key.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    await api_key_service.delete_api_key(db, key)
    await db.commit()

    await audit_service.log_action(
        db, organization_id=user.organization_id, actor_id=user.id,
        action="api_key.delete", resource_type="api_key", resource_id=str(key_id),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

@router.get("/audit-logs", response_model=Page[AuditLogRead])
async def list_audit_logs(
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Page[AuditLogRead]:
    """List audit log entries for the organization."""
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    items, total = await audit_service.list_audit_logs(
        db,
        organization_id=user.organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=eff_limit,
        offset=offset,
    )

    return Page[AuditLogRead](
        items=[AuditLogRead.model_validate(x) for x in items],
        total=total,
        limit=eff_limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Organization Members
# ---------------------------------------------------------------------------

@router.get("/organizations/me/members", response_model=list[MemberRead])
async def list_members(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberRead]:
    """List members of the current organization."""
    members = await enterprise_service.list_members(
        db, organization_id=user.organization_id
    )
    return [MemberRead.model_validate(m) for m in members]


_OWNER_ROLES = {"owner"}
_ADMIN_ROLES = {"owner", "admin"}


@router.patch("/organizations/me/members/{member_id}", response_model=MemberRead)
async def update_member_role(
    member_id: UUID,
    payload: MemberRoleUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> MemberRead:
    """Update a member's role. Only owners can change roles."""
    if user.role not in _ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only admins can change roles")

    member = await org_service.get_user(db, member_id)
    if not member or member.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member not found")

    if member.role in _OWNER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cannot change owner role")

    updated = await enterprise_service.update_member_role(db, member, payload.role)
    await db.commit()

    await audit_service.log_action(
        db, organization_id=user.organization_id, actor_id=user.id,
        action="member.role_update", resource_type="user", resource_id=str(member_id),
        details={"old_role": member.role, "new_role": payload.role},
    )

    return MemberRead.model_validate(updated)


@router.delete("/organizations/me/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Remove a member from the organization. Only owners/admins can remove."""
    if user.role not in _ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only admins can remove members")

    member = await org_service.get_user(db, member_id)
    if not member or member.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member not found")

    if member.role in _OWNER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cannot remove owner")

    if member.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot remove yourself")

    await enterprise_service.remove_member(db, member)

    await audit_service.log_action(
        db, organization_id=user.organization_id, actor_id=user.id,
        action="member.remove", resource_type="user", resource_id=str(member_id),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Organization Invitations
# ---------------------------------------------------------------------------

@router.post("/organizations/me/invitations", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InvitationCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationRead:
    """Invite someone to the organization. Only admins/owners can invite."""
    if user.role not in _ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only admins can invite")

    usage = await enterprise_service.get_org_usage(
        db, organization_id=user.organization_id
    )
    if usage["members"] >= usage["member_limit"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Member limit reached for your plan",
        )

    invitation = await enterprise_service.create_invitation(
        db,
        organization_id=user.organization_id,
        invited_by=user.id,
        email=payload.email,
        role=payload.role,
    )
    await db.commit()

    await audit_service.log_action(
        db, organization_id=user.organization_id, actor_id=user.id,
        action="invitation.create", resource_type="invitation", resource_id=str(invitation.id),
        details={"email": payload.email, "role": payload.role},
    )

    return InvitationRead.model_validate(invitation)


@router.get("/organizations/me/invitations", response_model=list[InvitationRead])
async def list_invitations(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[InvitationRead]:
    """List pending invitations for the organization."""
    invitations = await enterprise_service.list_invitations(
        db, organization_id=user.organization_id
    )
    return [InvitationRead.model_validate(i) for i in invitations]


@router.post("/invitations/accept", response_model=dict)
async def accept_invitation(
    payload: InvitationAccept,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Accept an invitation using its token."""
    invitation = await enterprise_service.accept_invitation(
        db, token=payload.token, user=user
    )
    if not invitation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expired invitation")
    await db.commit()
    return {"ok": True, "organization_id": str(invitation.organization_id)}


@router.delete("/organizations/me/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Revoke a pending invitation."""
    from helix.models.enterprise import OrganizationInvitation

    q = select(OrganizationInvitation).where(OrganizationInvitation.id == invitation_id)
    result = await db.execute(q)
    invitation = result.scalar_one_or_none()

    if not invitation or invitation.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invitation not found")

    await db.delete(invitation)
    await db.commit()

    await audit_service.log_action(
        db, organization_id=user.organization_id, actor_id=user.id,
        action="invitation.revoke", resource_type="invitation", resource_id=str(invitation_id),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Organization Usage
# ---------------------------------------------------------------------------

@router.get("/usage", response_model=UsageRead)
async def get_usage(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> UsageRead:
    """Get current organization usage against plan limits."""
    sub = await get_or_create_subscription(db, user.organization_id)
    usage = await enterprise_service.get_org_usage(
        db, organization_id=user.organization_id, plan=sub.plan
    )
    return UsageRead(**usage)


# ---------------------------------------------------------------------------
# Rate limit info
# ---------------------------------------------------------------------------

@router.get("/rate-limit")
async def get_rate_limit_info(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the rate limit for the current plan."""
    sub = await get_or_create_subscription(db, user.organization_id)
    rpm = get_rate_limit_for_plan(sub.plan)
    return {"plan": sub.plan, "requests_per_minute": rpm}
