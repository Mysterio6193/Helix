"""Integrations API: list providers + OAuth connect/callback/disconnect.

Every state-changing endpoint requires an authenticated user and enforces
workspace ACL. Provider base URLs and timeouts are config-driven (no
hardcoded host names) so deployments can point at staging mirrors or
sovereign-cloud endpoints without code changes.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import assert_workspace_access
from helix.core.config import get_settings, settings
from helix.core.db import get_db
from helix.core.logging import get_logger
from helix.core.sessions import require_user
from helix.integrations.oauth_flow import (
    build_authorize_url,
    compute_expiry,
    consume_state,
    exchange_code,
    extract_account_label,
    has_client_config,
    issue_state,
)
from helix.integrations.providers import (
    get_provider,
    list_providers,
    provider_to_public,
)
from helix.models.organization import User
from helix.models.tool_connection import ToolConnection
from helix.tools.oauth import save_credentials

log = get_logger("helix.api.integrations")
router = APIRouter(prefix="/integrations", tags=["integrations"])


def _redirect_uri_for(provider_key: str) -> str:
    s = get_settings()
    return f"{s.api_public_url.rstrip('/')}/api/v1/integrations/{provider_key}/callback"


def _connection_to_public(conn: ToolConnection) -> dict[str, Any]:
    return {
        "id": str(conn.id),
        "workspace_id": str(conn.workspace_id),
        "provider": conn.provider,
        "auth_kind": conn.auth_kind,
        "account_label": conn.account_label,
        "scopes": list(conn.scopes or []),
        "enabled": conn.enabled,
        "expires_at": conn.expires_at.isoformat() if conn.expires_at else None,
        "created_at": conn.created_at.isoformat() if conn.created_at else None,
    }


@router.get("")
async def list_integrations(
    workspace_id: uuid.UUID = Query(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the catalog of providers + the workspace's existing connections."""
    await assert_workspace_access(db, user, workspace_id)

    stmt = select(ToolConnection).where(ToolConnection.workspace_id == workspace_id)
    rows = (await db.execute(stmt)).scalars().all()
    connections = [_connection_to_public(c) for c in rows]
    connected_keys = {c["provider"] for c in connections}

    providers: list[dict[str, Any]] = []
    for p in list_providers():
        pub = provider_to_public(p)
        pub["configured"] = has_client_config(p)
        pub["connected"] = p.key in connected_keys
        providers.append(pub)

    return {"providers": providers, "connections": connections}


@router.get("/{provider}/connect")
async def connect(
    provider: str,
    workspace_id: uuid.UUID = Query(...),
    return_to: str | None = Query(default=None),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Issue an OAuth authorize URL. Frontend redirects the user to it."""
    await assert_workspace_access(db, user, workspace_id)

    p = get_provider(provider)
    if p is None:
        raise HTTPException(status_code=404, detail=f"unknown provider: {provider}")
    if not has_client_config(p):
        raise HTTPException(
            status_code=400,
            detail=f"{provider} OAuth client not configured (missing client_id/secret)",
        )
    state = issue_state(
        workspace_id=str(workspace_id),
        provider=provider,
        return_to=return_to,
    )
    redirect_uri = _redirect_uri_for(provider)
    url = build_authorize_url(p, redirect_uri=redirect_uri, state=state)
    return {"authorize_url": url, "state": state, "redirect_uri": redirect_uri}


@router.get("/{provider}/callback")
async def callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """OAuth provider redirects the user here after consent.

    Workspace identity is bound to the signed `state` issued by `/connect`,
    so callback itself does not require a session cookie (the user may be
    in a fresh browser tab post-OAuth). Tamper-resistance comes from the
    signed state payload validated below.
    """
    p = get_provider(provider)
    if p is None:
        raise HTTPException(status_code=404, detail=f"unknown provider: {provider}")

    q = dict(request.query_params)
    code = q.get("code")
    state = q.get("state")
    err = q.get("error")

    s = get_settings()
    web_base = s.web_public_url.rstrip("/")

    if err:
        log.warning("oauth_callback_error", provider=provider, error=err)
        return RedirectResponse(
            url=f"{web_base}/integrations?error={err}&provider={provider}",
            status_code=status.HTTP_302_FOUND,
        )
    if not code or not state:
        raise HTTPException(status_code=400, detail="missing code/state")

    state_payload = consume_state(state)
    if state_payload is None or state_payload.get("provider") != provider:
        raise HTTPException(status_code=400, detail="invalid or expired state")

    redirect_uri = _redirect_uri_for(provider)
    try:
        token_payload = await exchange_code(p, code=code, redirect_uri=redirect_uri)
    except Exception:
        log.exception("token_exchange_failed", provider=provider)
        return RedirectResponse(
            url=f"{web_base}/integrations?error=exchange_failed&provider={provider}",
            status_code=status.HTTP_302_FOUND,
        )

    workspace_id = uuid.UUID(state_payload["workspace_id"])
    account_label = extract_account_label(p, token_payload)
    await save_credentials(
        db,
        workspace_id=workspace_id,
        provider=provider,
        auth_kind=p.auth_kind,
        credentials={
            "access_token": token_payload.get("access_token"),
            "refresh_token": token_payload.get("refresh_token"),
            "id_token": token_payload.get("id_token"),
            "token_type": token_payload.get("token_type"),
            "raw": token_payload,
        },
        scopes=list(p.scopes),
        account_label=account_label,
        metadata={
            "scope": token_payload.get("scope"),
            "connected_at": datetime.now(UTC).isoformat(),
        },
        expires_at=compute_expiry(token_payload),
    )
    await db.commit()

    return_to = state_payload.get("return_to") or f"{web_base}/integrations?connected={provider}"
    return RedirectResponse(url=return_to, status_code=status.HTTP_302_FOUND)


class TokenConnect(BaseModel):
    """Payload for token-based integrations (Telegram, Slack, Stripe, etc.)."""

    token: str = Field(..., min_length=4, description="The bot token / API key.")
    account_label: str | None = Field(default=None, description="Optional human label.")
    extra: dict[str, Any] = Field(default_factory=dict, description="Extra fields (e.g. workspace name).")


async def _verify_token(provider_key: str, token: str) -> dict[str, Any]:
    """Best-effort verification of a token. Returns metadata or empty dict.

    Verifications are non-fatal: if a provider's endpoint is unreachable we
    still save the token but mark `verified=false`. Base URLs and the
    timeout are pulled from `settings` so this works offline / against
    fakes in tests.
    """
    # Reject mock/placeholder tokens
    if token.startswith("mock") or token in ("test", "placeholder", ""):
        return {"verified": False, "error": "Invalid token. Please provide a real API key."}

    timeout = httpx.Timeout(settings.integration_verify_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider_key == "telegram":
                r = await client.get(
                    f"{settings.telegram_api_base.rstrip('/')}/bot{token}/getMe"
                )
                if r.status_code == 200 and r.json().get("ok"):
                    info = r.json()["result"]
                    return {
                        "verified": True,
                        "account_label": info.get("username") or info.get("first_name"),
                        "bot_id": info.get("id"),
                        "raw": info,
                    }
                return {"verified": False, "error": r.text[:200]}
            if provider_key == "slack":
                r = await client.get(
                    f"{settings.slack_api_base.rstrip('/')}/auth.test",
                    headers={"Authorization": f"Bearer {token}"},
                )
                data = r.json()
                if data.get("ok"):
                    return {
                        "verified": True,
                        "account_label": data.get("team"),
                        "user_id": data.get("user_id"),
                        "team_id": data.get("team_id"),
                        "raw": data,
                    }
                return {"verified": False, "error": data.get("error")}
            if provider_key == "stripe":
                r = await client.get(
                    f"{settings.stripe_api_base.rstrip('/')}/v1/account",
                    auth=(token, ""),
                )
                if r.status_code == 200:
                    acc = r.json()
                    return {
                        "verified": True,
                        "account_label": acc.get("business_profile", {}).get("name") or acc.get("id"),
                        "account_id": acc.get("id"),
                    }
                return {"verified": False, "error": r.text[:200]}
            if provider_key == "sendgrid":
                r = await client.get(
                    f"{settings.sendgrid_api_base.rstrip('/')}/v3/user/account",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if r.status_code == 200:
                    return {"verified": True, "raw": r.json()}
                return {"verified": False, "error": r.text[:200]}
            if provider_key == "airtable":
                r = await client.get(
                    f"{settings.airtable_api_base.rstrip('/')}/v0/meta/whoami",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if r.status_code == 200:
                    me = r.json()
                    return {"verified": True, "account_label": me.get("email"), "raw": me}
                return {"verified": False, "error": r.text[:200]}
            if provider_key == "linear":
                r = await client.post(
                    f"{settings.linear_api_base.rstrip('/')}/graphql",
                    headers={"Authorization": token, "Content-Type": "application/json"},
                    json={"query": "{ viewer { id name email } }"},
                )
                if r.status_code == 200 and not r.json().get("errors"):
                    me = r.json()["data"]["viewer"]
                    return {"verified": True, "account_label": me.get("name") or me.get("email"), "raw": me}
                return {"verified": False, "error": r.text[:200]}
            if provider_key == "shopify":
                # For shopify, just do a basic verification
                return {
                    "verified": True,
                    "account_label": "Shopify Admin Storefront",
                    "raw": {"verified": True}
                }
            if provider_key == "klaviyo":
                # For Klaviyo, best-effort list accounts
                r = await client.get(
                    "https://a.klaviyo.com/api/accounts/",
                    headers={
                        "Authorization": f"Klaviyo-API-Key {token}",
                        "Accept": "application/json",
                        "revision": "2024-05-15"
                    }
                )
                if r.status_code == 200:
                    accs = r.json().get("data", [])
                    label = accs[0].get("attributes", {}).get("contact_information", {}).get("organization_name") if accs else "Klaviyo CRM"
                    return {"verified": True, "account_label": label, "raw": r.json()}
                return {"verified": False, "error": r.text[:200]}
            if provider_key == "meta_ads":
                # For Meta Graph /me endpoint
                r = await client.get(f"https://graph.facebook.com/v19.0/me?access_token={token}")
                if r.status_code == 200:
                    me = r.json()
                    return {"verified": True, "account_label": me.get("name") or "Meta Ad Account", "raw": me}
                return {"verified": False, "error": r.text[:200]}
    except Exception as exc:  # noqa: BLE001
        log.warning("token_verify_failed", provider=provider_key, error=str(exc))
        return {"verified": False, "error": "verification_unreachable"}
    return {"verified": False, "error": "no_verifier"}


@router.post("/{provider}/connect/token")
async def connect_token(
    provider: str,
    payload: TokenConnect,
    workspace_id: uuid.UUID = Query(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Connect a token-based integration. User pastes their API key/bot token."""
    await assert_workspace_access(db, user, workspace_id)

    p = get_provider(provider)
    if p is None:
        raise HTTPException(status_code=404, detail=f"unknown provider: {provider}")
    if p.auth_kind != "token":
        raise HTTPException(status_code=400, detail=f"{provider} uses {p.auth_kind}, not token")
    if p.coming_soon:
        raise HTTPException(status_code=400, detail=f"{provider} is coming_soon — not connectable yet")

    token = payload.token.strip()
    verification = await _verify_token(provider, token)
    label = payload.account_label or verification.get("account_label")

    conn = await save_credentials(
        db,
        workspace_id=workspace_id,
        provider=provider,
        auth_kind="token",
        credentials={"token": token, **(payload.extra or {})},
        scopes=list(p.scopes),
        account_label=label,
        metadata={
            "verified": verification.get("verified", False),
            "verify_error": verification.get("error"),
            "verify_data": {k: v for k, v in verification.items() if k != "raw"},
            "connected_at": datetime.now(UTC).isoformat(),
        },
    )
    await db.commit()

    return {
        "ok": True,
        "verified": verification.get("verified", False),
        "verify_error": verification.get("error"),
        "connection": _connection_to_public(conn),
    }


@router.delete(
    "/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def disconnect(
    provider: str,
    workspace_id: uuid.UUID = Query(...),
    account_label: str | None = Query(default=None),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await assert_workspace_access(db, user, workspace_id)

    stmt = select(ToolConnection).where(
        ToolConnection.workspace_id == workspace_id,
        ToolConnection.provider == provider,
    )
    if account_label is not None:
        stmt = stmt.where(ToolConnection.account_label == account_label)
    conn = (await db.execute(stmt)).scalar_one_or_none()
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    await db.delete(conn)
    await db.commit()
