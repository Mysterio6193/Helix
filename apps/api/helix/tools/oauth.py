"""OAuth helper: store/refresh provider credentials in tool_connections."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.security import decrypt, encrypt
from helix.models.tool_connection import ToolConnection


async def save_credentials(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    provider: str,
    auth_kind: str,
    credentials: dict[str, Any],
    scopes: list[str] | None = None,
    account_label: str | None = None,
    metadata: dict[str, Any] | None = None,
    expires_at: datetime | None = None,
) -> ToolConnection:
    encrypted = encrypt(json.dumps(credentials))

    stmt = select(ToolConnection).where(
        ToolConnection.workspace_id == workspace_id,
        ToolConnection.provider == provider,
        ToolConnection.account_label == account_label,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing is None:
        conn = ToolConnection(
            workspace_id=workspace_id,
            provider=provider,
            auth_kind=auth_kind,
            account_label=account_label,
            credentials_encrypted=encrypted,
            scopes=scopes or [],
            metadata_=metadata or {},
            expires_at=expires_at,
        )
        db.add(conn)
    else:
        existing.credentials_encrypted = encrypted
        existing.auth_kind = auth_kind
        existing.scopes = scopes or existing.scopes
        existing.metadata_ = {**(existing.metadata_ or {}), **(metadata or {})}
        existing.expires_at = expires_at
        conn = existing
    await db.flush()
    await db.refresh(conn)
    return conn


async def load_credentials(
    db: AsyncSession, *, workspace_id: uuid.UUID, provider: str, account_label: str | None = None
) -> dict[str, Any] | None:
    stmt = select(ToolConnection).where(
        ToolConnection.workspace_id == workspace_id,
        ToolConnection.provider == provider,
        ToolConnection.enabled.is_(True),
    )
    if account_label is not None:
        stmt = stmt.where(ToolConnection.account_label == account_label)
    conn = (await db.execute(stmt)).scalar_one_or_none()
    if conn is None:
        return None
    plain = decrypt(conn.credentials_encrypted)
    try:
        return json.loads(plain)
    except json.JSONDecodeError:
        return None
