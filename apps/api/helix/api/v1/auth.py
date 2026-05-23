"""Auth endpoints: Google OAuth sign-in/sign-up + session management."""
from __future__ import annotations

import secrets
from typing import Any, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import settings
from helix.core.db import get_db
from helix.core.logging import get_logger
from helix.core.sessions import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    get_current_user,
    issue_session,
)
from helix.models.organization import Organization, User, Workspace

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("helix.auth")

# OAuth endpoints come from config so deployments can override them.
OAUTH_STATE_COOKIE = "helix_oauth_state"
OAUTH_RETURN_COOKIE = "helix_oauth_return"


class AuthStatus(BaseModel):
    authenticated: bool
    provider: Optional[str] = None
    user: Optional[dict] = None


class AuthURL(BaseModel):
    url: str


def _redirect_uri() -> str:
    """Route OAuth callback through the web origin via Next.js rewrites so the
    `Set-Cookie` response lands on the browser-facing domain instead of the API.

    Override with HELIX_OAUTH_REDIRECT_URI for non-standard deployments.
    """
    return f"{settings.web_public_url.rstrip('/')}/api/proxy/auth/google/callback"


def _safe_return_to(value: Optional[str]) -> str:
    if not value:
        return "/"
    # Only allow same-origin paths
    if value.startswith("/") and not value.startswith("//"):
        return value
    return "/"


@router.get("/google/start", response_model=AuthURL)
async def google_start(return_to: str = "/") -> AuthURL:
    """Begin Google OAuth — returns the URL the client should redirect to."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google_oauth_not_configured",
        )
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
        "state": state,
    }
    url = f"{settings.google_auth_url}?{urlencode(params)}"
    resp = AuthURL(url=url)
    # Stash state + return_to in a short-lived cookie so callback can verify
    response = Response(content=resp.model_dump_json(), media_type="application/json")
    response.set_cookie(OAUTH_STATE_COOKIE, state, max_age=600, httponly=True, samesite="lax", path="/")
    response.set_cookie(OAUTH_RETURN_COOKIE, _safe_return_to(return_to), max_age=600, httponly=True, samesite="lax", path="/")
    return response  # type: ignore[return-value]


async def _ensure_default_org(db: AsyncSession) -> Organization:
    """Get or create the default `helix` organization + default workspace."""
    stmt = select(Organization).where(Organization.slug == "helix")
    org = (await db.execute(stmt)).scalar_one_or_none()
    if org is None:
        org = Organization(name="Helix", slug="helix", metadata_={})
        db.add(org)
        await db.flush()
        ws = Workspace(
            organization_id=org.id,
            name="Default",
            slug="default",
            description="Default workspace",
            settings={},
        )
        db.add(ws)
        await db.flush()
    return org


async def _upsert_user(db: AsyncSession, *, email: str, name: Optional[str], google_id: str, picture: Optional[str]) -> User:
    org = await _ensure_default_org(db)
    stmt = select(User).where(User.email == email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None:
        user = User(
            organization_id=org.id,
            email=email,
            name=name,
            role="owner",
            metadata_={"google_id": google_id, "picture": picture, "provider": "google"},
        )
        db.add(user)
        await db.flush()
        log.info("auth.user_created", email=email, user_id=str(user.id))
    else:
        meta = dict(user.metadata_ or {})
        meta["google_id"] = google_id
        meta["provider"] = "google"
        if picture:
            meta["picture"] = picture
        user.metadata_ = meta
        if name and not user.name:
            user.name = name
        log.info("auth.user_logged_in", email=email, user_id=str(user.id))
    await db.commit()
    return user


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    helix_oauth_state: Optional[str] = Cookie(default=None, alias=OAUTH_STATE_COOKIE),
    helix_oauth_return: Optional[str] = Cookie(default=None, alias=OAUTH_RETURN_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Google OAuth callback — exchanges code for tokens, upserts user, issues session."""
    web_base = settings.web_public_url.rstrip("/")
    if error:
        return RedirectResponse(f"{web_base}/sign-in?error={error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="missing_code_or_state")
    if not helix_oauth_state or not secrets.compare_digest(state, helix_oauth_state):
        raise HTTPException(status_code=400, detail="invalid_state")
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="google_oauth_not_configured")

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            settings.google_token_url,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": _redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            log.warning("auth.token_exchange_failed", body=token_resp.text)
            raise HTTPException(status_code=400, detail="token_exchange_failed")
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="no_access_token")

        info_resp = await client.get(
            settings.google_userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if info_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="userinfo_failed")
        info = info_resp.json()

    email = info.get("email")
    if not email or not info.get("email_verified", True):
        raise HTTPException(status_code=400, detail="email_not_verified")

    user = await _upsert_user(
        db,
        email=email,
        name=info.get("name"),
        google_id=info.get("sub", ""),
        picture=info.get("picture"),
    )

    return_to = _safe_return_to(helix_oauth_return)
    session_token = issue_session(str(user.id))

    response = RedirectResponse(f"{web_base}{return_to}", status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/")
    response.delete_cookie(OAUTH_RETURN_COOKIE, path="/")
    return response


@router.get("/me", response_model=AuthStatus)
async def me(user: Optional[User] = Depends(get_current_user)) -> AuthStatus:
    if user is None:
        return AuthStatus(authenticated=False)
    meta = user.metadata_ or {}
    return AuthStatus(
        authenticated=True,
        provider=meta.get("provider"),
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "picture": meta.get("picture"),
            "organization_id": str(user.organization_id),
        },
    )


@router.post("/logout")
async def logout() -> Response:
    resp = Response(content='{"ok":true}', media_type="application/json")
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@router.get("/providers")
async def providers() -> dict:
    return {
        "google": {
            "enabled": bool(settings.google_client_id and settings.google_client_secret),
            "label": "Continue with Google",
        }
    }


class DevBypassInput(BaseModel):
    email: str
    name: str


@router.post("/dev-bypass")
async def dev_bypass(
    payload: DevBypassInput,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Allows simulated developer logins when running locally or in development."""
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev bypass is not allowed in production",
        )

    email = payload.email.strip()
    name = payload.name.strip()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email_required",
        )

    # Simulated Google profile photo or a gorgeous fallback avatar from Unsplash
    # to feel incredibly premium!
    fallback_picture = (
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=256&h=256&q=80"
    )

    user = await _upsert_user(
        db,
        email=email,
        name=name or email.split("@")[0].capitalize(),
        google_id=f"dev-oauth-{email}",
        picture=fallback_picture,
    )

    session_token = issue_session(str(user.id))

    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )

    return {"ok": True, "user_id": str(user.id)}

