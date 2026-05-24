"""Audit log service."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.enterprise import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        organization_id=organization_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def list_audit_logs(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    q = select(AuditLog).where(AuditLog.organization_id == organization_id)
    count_q = select(func.count()).select_from(AuditLog).where(AuditLog.organization_id == organization_id)

    if action:
        q = q.where(AuditLog.action == action)
    if resource_type:
        q = q.where(AuditLog.resource_type == resource_type)
    if resource_id:
        q = q.where(AuditLog.resource_id == resource_id)
    if actor_id:
        q = q.where(AuditLog.actor_id == actor_id)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        q.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total
