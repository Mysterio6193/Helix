"""OAuth dance driver: builds authorize URLs, exchanges codes for tokens,
refreshes expired tokens. Per-provider quirks live in `providers.py`."""
from __future__ import annotations

import base64
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.integrations.providers import OAuthProvider

log = get_logger("helix.integrations.oauth")


# In-process state store for CSRF protection. Each item: state -> (workspace_id, provider, created_ts).
# Single-instance acceptable for now; persist to Redis in multi-worker deployments.
_STATE_STORE: dict[str, dict[str, Any]] = {}
_STATE_TTL_SEC = 600


def _purge_expired() -> None:
    now = time.time()
    expired = [s for s, v in _STATE_STORE.items() if now - v["created_ts"] > _STATE_TTL_SEC]
    for s in expired:
        _STATE_STORE.pop(s, None)


def issue_state(*, workspace_id: str, provider: str, return_to: str | None = None) -> str:
    _purge_expired()
    state = secrets.token_urlsafe(32)
    _STATE_STORE[state] = {
        "workspace_id": workspace_id,
        "provider": provider,
        "return_to": return_to,
        "created_ts": time.time(),
    }
    return state


def consume_state(state: str) -> dict[str, Any] | None:
    _purge_expired()
    return _STATE_STORE.pop(state, None)


def _client_credentials(provider: OAuthProvider) -> tuple[str, str]:
    s = get_settings()
    mapping = {
        "canva": (s.canva_client_id, s.canva_client_secret),
        "figma": (s.figma_client_id, s.figma_client_secret),
        "notion": (s.notion_client_id, s.notion_client_secret),
        "google": (s.google_client_id, s.google_client_secret),
    }
    return mapping.get(provider.key, ("", ""))


def has_client_config(provider: OAuthProvider) -> bool:
    # Token-based providers (Telegram, Slack bot, Stripe, etc.) are always
    # "configured" from a server-config standpoint — the user supplies the
    # secret at connect time.
    if provider.auth_kind == "token":
        return True
    client_id, client_secret = _client_credentials(provider)
    return bool(client_id and client_secret)


def build_authorize_url(provider: OAuthProvider, *, redirect_uri: str, state: str) -> str:
    client_id, _ = _client_credentials(provider)
    params: dict[str, str] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        **provider.extra_authorize_params,
    }
    if provider.scopes:
        params["scope"] = provider.scope_separator.join(provider.scopes)
    return f"{provider.authorize_url}?{urlencode(params)}"


async def exchange_code(
    provider: OAuthProvider,
    *,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    client_id, client_secret = _client_credentials(provider)
    body: dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        **provider.extra_token_params,
    }
    headers: dict[str, str] = {"Accept": "application/json"}

    if provider.uses_basic_auth_for_token:
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    else:
        body["client_id"] = client_id
        body["client_secret"] = client_secret

    async with httpx.AsyncClient(timeout=30) as http:
        if provider.token_body_format == "json":
            headers["Content-Type"] = "application/json"
            resp = await http.post(provider.token_url, headers=headers, json=body)
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            resp = await http.post(provider.token_url, headers=headers, data=body)

    if resp.status_code >= 400:
        log.warning(
            "oauth_exchange_failed",
            provider=provider.key,
            status=resp.status_code,
            body=resp.text[:500],
        )
        raise RuntimeError(f"{provider.key} token exchange {resp.status_code}: {resp.text}")
    payload = resp.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"{provider.key} token response not JSON object")
    return payload


async def refresh_token(
    provider: OAuthProvider,
    *,
    refresh_token_value: str,
) -> dict[str, Any]:
    client_id, client_secret = _client_credentials(provider)
    body: dict[str, str] = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_value,
    }
    headers: dict[str, str] = {"Accept": "application/json"}
    if provider.uses_basic_auth_for_token:
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    else:
        body["client_id"] = client_id
        body["client_secret"] = client_secret

    async with httpx.AsyncClient(timeout=30) as http:
        if provider.token_body_format == "json":
            headers["Content-Type"] = "application/json"
            resp = await http.post(provider.token_url, headers=headers, json=body)
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            resp = await http.post(provider.token_url, headers=headers, data=body)
    if resp.status_code >= 400:
        raise RuntimeError(f"{provider.key} refresh {resp.status_code}: {resp.text}")
    payload = resp.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"{provider.key} refresh response not JSON object")
    return payload


def compute_expiry(payload: dict[str, Any]) -> datetime | None:
    expires_in = payload.get("expires_in")
    if isinstance(expires_in, (int, float)):
        return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
    return None


def extract_account_label(provider: OAuthProvider, payload: dict[str, Any]) -> str | None:
    """Provider-specific best-effort label from the token response."""
    if provider.key == "notion":
        owner = payload.get("workspace_name") or (payload.get("owner") or {}).get("user", {}).get("name")
        return owner or payload.get("workspace_id")
    if provider.key == "figma":
        # Figma includes `user_id` only; the client should fetch /v1/me for a label later.
        return payload.get("user_id")
    # Canva + Google don't include a label in the token response.
    return None
