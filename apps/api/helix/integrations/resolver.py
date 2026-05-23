"""Resolve a workspace's access token for a provider.

Skills call `get_access_token(db, workspace_id, "notion")` and get back a
ready-to-use string. If the stored credentials are expired and a refresh
token is present, a refresh is attempted and the new credentials are
persisted before returning.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.integrations.oauth_flow import (
    compute_expiry,
    has_client_config,
    refresh_token,
)
from helix.integrations.providers import get_provider
from helix.models.tool_connection import ToolConnection
from helix.tools.oauth import save_credentials

log = get_logger("helix.integrations.resolver")


async def _load_connection(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    provider: str,
    account_label: str | None,
) -> ToolConnection | None:
    stmt = select(ToolConnection).where(
        ToolConnection.workspace_id == workspace_id,
        ToolConnection.provider == provider,
        ToolConnection.enabled.is_(True),
    )
    if account_label is not None:
        stmt = stmt.where(ToolConnection.account_label == account_label)
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_access_token(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    provider: str,
    account_label: str | None = None,
) -> str | None:
    """Return a usable access token for `provider`, refreshing if expired."""
    from helix.core.security import decrypt
    import json

    conn = await _load_connection(
        db, workspace_id=workspace_id, provider=provider, account_label=account_label
    )
    if conn is None:
        return None

    try:
        creds = json.loads(decrypt(conn.credentials_encrypted))
    except Exception:
        log.exception("creds_decrypt_failed", provider=provider)
        return None

    access_token = creds.get("access_token")
    refresh_value = creds.get("refresh_token")
    expires_at = conn.expires_at

    # Refresh if we have a refresh token and the token has expired (or is about to).
    needs_refresh = (
        expires_at is not None
        and refresh_value
        and expires_at <= datetime.now(timezone.utc)
    )
    if not needs_refresh:
        return access_token

    provider_def = get_provider(provider)
    if provider_def is None or not has_client_config(provider_def):
        return access_token

    try:
        refreshed = await refresh_token(provider_def, refresh_token_value=refresh_value)
    except Exception:
        log.exception("token_refresh_failed", provider=provider)
        return access_token

    new_access = refreshed.get("access_token") or access_token
    new_refresh = refreshed.get("refresh_token") or refresh_value
    merged: dict[str, Any] = {**creds, "access_token": new_access, "refresh_token": new_refresh}
    await save_credentials(
        db,
        workspace_id=workspace_id,
        provider=provider,
        auth_kind=conn.auth_kind,
        credentials=merged,
        scopes=conn.scopes,
        account_label=conn.account_label,
        metadata={"refreshed_at": datetime.now(timezone.utc).isoformat()},
        expires_at=compute_expiry(refreshed),
    )
    await db.commit()
    return new_access
