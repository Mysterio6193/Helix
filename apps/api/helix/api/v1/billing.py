"""Billing API endpoints — Stripe-backed subscriptions."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core import billing as billing_service
from helix.core.billing import BillingNotConfigured, get_billing_period_usage, get_public_plans
from helix.core.config import settings
from helix.core.db import get_db
from helix.core.logging import get_logger
from helix.core.sessions import get_current_user
from helix.models.organization import Organization, User

router = APIRouter(prefix="/billing", tags=["billing"])
log = get_logger("helix.api.billing")


class CheckoutCreate(BaseModel):
    plan: str
    success_url: str | None = None
    cancel_url: str | None = None


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class SubscriptionStatus(BaseModel):
    plan: str
    status: str
    cancel_at_period_end: bool
    current_period_end: str | None = None
    stripe_customer_id: str | None = None
    has_active_subscription: bool
    publishable_key: str | None = None


def _require_user(user: User | None) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="not_authenticated")
    return user


async def _load_org(db: AsyncSession, user: User) -> Organization:
    org = (
        await db.execute(
            select(Organization).where(Organization.id == user.organization_id)
        )
    ).scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="organization_not_found")
    return org


@router.get("/plans")
async def list_plans() -> dict[str, Any]:
    """Public plan catalog. Each plan reports whether it's available
    (i.e., its Stripe price ID has been configured)."""
    return {
        "plans": get_public_plans(),
        "stripe_configured": bool(settings.stripe_secret_key),
        "publishable_key": settings.stripe_publishable_key or None,
    }


@router.get("/subscription", response_model=SubscriptionStatus)
async def get_subscription(
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStatus:
    """Current subscription state for the authenticated user's org."""
    u = _require_user(user)
    sub = await billing_service.get_or_create_subscription(db, u.organization_id)
    active = sub.status in ("active", "trialing") and sub.plan != "free"
    return SubscriptionStatus(
        plan=sub.plan,
        status=sub.status,
        cancel_at_period_end=sub.cancel_at_period_end,
        current_period_end=(
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
        stripe_customer_id=sub.stripe_customer_id,
        has_active_subscription=active,
        publishable_key=settings.stripe_publishable_key or None,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutCreate,
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Start a Stripe Checkout flow for the chosen plan."""
    u = _require_user(user)
    org = await _load_org(db, u)

    web_base = settings.web_public_url.rstrip("/")
    success_url = payload.success_url or (
        f"{web_base}/settings/billing?checkout=success&session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = payload.cancel_url or f"{web_base}/settings/billing?checkout=cancelled"

    try:
        url = await billing_service.create_checkout_session(
            db,
            organization=org,
            user=u,
            plan=payload.plan,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except BillingNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # pragma: no cover - surface Stripe errors
        log.exception("billing.checkout_failed", plan=payload.plan)
        raise HTTPException(status_code=400, detail=f"checkout_failed: {exc}")

    return CheckoutResponse(url=url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortalResponse:
    """Open the Stripe Customer Portal so the user can manage payment + cancel."""
    u = _require_user(user)
    org = await _load_org(db, u)
    web_base = settings.web_public_url.rstrip("/")
    return_url = f"{web_base}/settings/billing"
    try:
        url = await billing_service.create_portal_session(
            db, organization=org, user=u, return_url=return_url
        )
    except BillingNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return PortalResponse(url=url)


@router.get("/usage")
async def billing_usage(
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Usage stats for the current billing period."""
    u = _require_user(user)
    return await get_billing_period_usage(db, u.organization_id)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Stripe webhook endpoint. Configure in Stripe dashboard:
    URL: {API_PUBLIC_URL}/api/v1/billing/webhook"""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="missing_signature")
    payload = await request.body()
    try:
        event = billing_service.verify_webhook_signature(payload, stripe_signature)
    except BillingNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        log.warning("billing.webhook.invalid_signature", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_signature",
        )

    try:
        await billing_service.handle_webhook_event(db, event)
    except Exception:
        log.exception("billing.webhook.handler_failed", event_id=event.get("id"))
        # Return 200 anyway so Stripe doesn't retry storms on a logic bug.
        # The event won't be marked processed, so a manual replay can fix it.
        return {"received": True, "processed": False}

    return {"received": True, "processed": True}
