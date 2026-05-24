"""Signed session cookies for end-user auth.

Format: base64url(json_payload).base64url(hmac_sha256(payload, secret))
Payload: {"uid": str, "exp": int_unix_seconds}

No third-party deps — uses stdlib hmac + hashlib + base64.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import UTC
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import settings
from helix.core.db import get_db
from helix.models.organization import User

# Cookie name + TTL are now driven by config so deployments can rotate them
# without code changes. The exported constants remain for backwards-compat
# imports (they resolve to the current settings values at import time).
SESSION_COOKIE = settings.session_cookie_name
SESSION_TTL_SECONDS = settings.session_ttl_seconds


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(s: str) -> bytes:
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)


def _sign(payload: bytes) -> bytes:
    return hmac.new(settings.secret_key.encode("utf-8"), payload, hashlib.sha256).digest()


def issue_session(user_id: str, ttl: int = SESSION_TTL_SECONDS) -> str:
    payload = {"uid": str(user_id), "exp": int(time.time()) + ttl}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = _sign(raw)
    return f"{_b64encode(raw)}.{_b64encode(sig)}"


def verify_session(token: str) -> dict | None:
    try:
        body_b64, sig_b64 = token.split(".", 1)
        body = _b64decode(body_b64)
        expected = _sign(body)
        if not hmac.compare_digest(expected, _b64decode(sig_b64)):
            return None
        payload = json.loads(body)
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


async def _resolve_api_key(db: AsyncSession, raw_key: str) -> User | None:
    """Resolve an API key to a User, or return None."""
    import hashlib

    from sqlalchemy import select

    from helix.models.enterprise import ApiKey

    if not raw_key.startswith("helix_"):
        return None

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.enabled.is_(True),
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        return None

    user = await db.get(User, key.user_id)
    if user:
        from datetime import datetime
        key.last_used_at = datetime.now(UTC)
        await db.flush()
    return user


async def get_current_user(
    request: Request,
    helix_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Returns User if a valid session cookie or API key is present, else None.

    Use this for endpoints where auth is optional (read-mostly).
    """
    token = helix_session
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
    if not token:
        return None

    # Try session cookie first
    payload = verify_session(token)
    if payload:
        try:
            user = await db.get(User, UUID(payload["uid"]))
            if user:
                return user
        except Exception:
            pass

    # Fall back to API key
    user = await _resolve_api_key(db, token)
    return user


async def require_user(
    user: User | None = Depends(get_current_user),
) -> User:
    """Use this for endpoints that require a logged-in user."""
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    return user
