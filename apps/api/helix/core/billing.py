"""Stripe billing service.

Thin wrapper around the Stripe SDK. Centralizes:
 - Plan tier <-> Stripe price ID mapping
 - Checkout session creation
 - Customer portal session creation
 - Webhook signature verification + event handling
 - Local Subscription mirror updates
 - Quota enforcement for LLM endpoints
 - Metered usage reporting to Stripe

Keep this file Stripe-specific. The API router calls into here so endpoints
don't have to deal with the SDK directly.
"""
from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import settings
from helix.core.logging import get_logger
from helix.models.billing import (
    PLAN_BUSINESS,
    PLAN_FREE,
    PLAN_PRO,
    PLAN_STARTER,
    SUB_STATUS_ACTIVE,
    SUB_STATUS_CANCELED,
    BillingEvent,
    Subscription,
)
from helix.models.organization import Organization, User
from helix.models.usage import UsageRecord

log = get_logger("helix.billing")

# Lazy stripe import so the API can boot without the SDK installed.
# In production, add `stripe>=8.0` to apps/api/pyproject.toml.
try:
    import stripe as _stripe  # type: ignore
except Exception:  # pragma: no cover
    _stripe = None


class BillingNotConfigured(RuntimeError):
    """Raised when Stripe is asked to do something but keys aren't set."""


def _stripe_client():
    if _stripe is None:
        raise BillingNotConfigured(
            "stripe SDK not installed. Add 'stripe>=8.0' to apps/api/pyproject.toml"
        )
    if not settings.stripe_secret_key:
        raise BillingNotConfigured("STRIPE_SECRET_KEY is not set")
    _stripe.api_key = settings.stripe_secret_key
    return _stripe


# --- Plan catalog ---------------------------------------------------------

# Single source of truth for plan metadata served to the frontend.
PLAN_CATALOG: list[dict[str, Any]] = [
    {
        "id": PLAN_FREE,
        "name": "Free",
        "price_cents": 0,
        "interval": "month",
        "tagline": "Kick the tires.",
        "features": [
            "1 brand",
            "10 workflow runs / month",
            "Community support",
        ],
        "limits": {"brands": 1, "runs_per_month": 10, "members": 1, "api_keys": 3},
        "stripe_price_id": None,
    },
    {
        "id": PLAN_STARTER,
        "name": "Starter",
        "price_cents": 4900,
        "interval": "month",
        "tagline": "For solo operators.",
        "features": [
            "5 brands",
            "200 workflow runs / month",
            "Email support",
            "All integrations",
        ],
        "limits": {"brands": 5, "runs_per_month": 200, "members": 5, "api_keys": 10},
        "stripe_price_id_setting": "stripe_price_starter",
    },
    {
        "id": PLAN_PRO,
        "name": "Pro",
        "price_cents": 14900,
        "interval": "month",
        "tagline": "For growing brands.",
        "features": [
            "25 brands",
            "1,500 workflow runs / month",
            "Priority support",
            "Custom design systems",
        ],
        "limits": {"brands": 25, "runs_per_month": 1500, "members": 25, "api_keys": 50},
        "stripe_price_id_setting": "stripe_price_pro",
        "highlight": True,
    },
    {
        "id": PLAN_BUSINESS,
        "name": "Business",
        "price_cents": 49900,
        "interval": "month",
        "tagline": "For agencies & teams.",
        "features": [
            "Unlimited brands",
            "10,000 workflow runs / month",
            "SLA + dedicated support",
            "SSO + audit logs",
        ],
        "limits": {"brands": None, "runs_per_month": 10000, "members": None, "api_keys": 200},
        "stripe_price_id_setting": "stripe_price_business",
    },
]


def get_public_plans() -> list[dict[str, Any]]:
    """Return plans with Stripe price IDs filled in (omitting unconfigured ones)."""
    plans: list[dict[str, Any]] = []
    for plan in PLAN_CATALOG:
        out = {k: v for k, v in plan.items() if k != "stripe_price_id_setting"}
        setting_key = plan.get("stripe_price_id_setting")
        if setting_key:
            price_id = getattr(settings, setting_key, "")
            out["stripe_price_id"] = price_id or None
            out["available"] = bool(price_id)
        else:
            out["available"] = True
        plans.append(out)
    return plans


def get_plan_limits(plan: str = PLAN_FREE) -> dict:
    """Return the limit dict for a given plan tier."""
    for p in PLAN_CATALOG:
        if p["id"] == plan:
            return p["limits"]
    return {"brands": 1, "runs_per_month": 10, "members": 1, "api_keys": 3}


def plan_from_price_id(price_id: str) -> str:
    """Map a Stripe price ID back to an internal plan tier."""
    mapping = {
        settings.stripe_price_starter: PLAN_STARTER,
        settings.stripe_price_pro: PLAN_PRO,
        settings.stripe_price_business: PLAN_BUSINESS,
    }
    return mapping.get(price_id, PLAN_FREE)


# --- Quota enforcement ---------------------------------------------------


async def check_llm_quota(
    db: AsyncSession, organization_id
) -> dict:
    """Check whether this org has remaining quota for the current billing period.
    Returns dict with allowed boolean and usage stats."""
    sub = await get_or_create_subscription(db, organization_id)
    limits = get_plan_limits(sub.plan)
    run_limit = limits.get("runs_per_month", 50)

    now = datetime.now(UTC)
    period_start = sub.current_period_end - timedelta(days=30) if sub.current_period_end else now.replace(day=1)
    if period_start > now:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if run_limit is None:
        return {"allowed": True, "limit": None, "used": 0, "remaining": None}

    used = (
        await db.execute(
            select(func.count(UsageRecord.id))
            .where(
                UsageRecord.organization_id == organization_id,
                UsageRecord.created_at >= period_start,
            )
        )
    ).scalar_one() or 0

    remaining = max(0, run_limit - used)

    return {"allowed": remaining > 0, "limit": run_limit, "used": used, "remaining": remaining}


async def report_metered_usage(organization_id, quantity: int, timestamp: datetime | None = None) -> bool:
    """Report usage to Stripe metered billing (non-blocking, fire-and-forget)."""
    if not settings.stripe_secret_key:
        return False
    try:
        stripe = _stripe_client()
        stripe.billing.MeterEvent.create(
            event_name="llm_calls",
            payload={
                "value": str(quantity),
                "stripe_customer_id": str(organization_id),
            },
            timestamp=timestamp or int(time.time()),
        )
        return True
    except Exception:
        log.warning("billing.meter_report_failed", org_id=str(organization_id))
        return False


async def get_billing_period_usage(
    db: AsyncSession, organization_id
) -> dict:
    """Aggregate usage stats for the current billing period."""
    sub = await get_or_create_subscription(db, organization_id)
    limits = get_plan_limits(sub.plan)
    now = datetime.now(UTC)
    period_start = sub.current_period_end - timedelta(days=30) if sub.current_period_end else now.replace(day=1)

    query = select(
        func.sum(UsageRecord.prompt_tokens).label("prompt_tokens"),
        func.sum(UsageRecord.completion_tokens).label("completion_tokens"),
        func.sum(UsageRecord.cost_usd).label("cost_usd"),
        func.count(UsageRecord.id).label("calls"),
    ).where(
        UsageRecord.organization_id == organization_id,
        UsageRecord.created_at >= period_start,
    )
    row = (await db.execute(query)).one()

    model_query = (
        select(
            UsageRecord.model_id,
            func.sum(UsageRecord.prompt_tokens).label("prompt_tokens"),
            func.sum(UsageRecord.completion_tokens).label("completion_tokens"),
            func.sum(UsageRecord.cost_usd).label("cost_usd"),
            func.count(UsageRecord.id).label("calls"),
        )
        .where(
            UsageRecord.organization_id == organization_id,
            UsageRecord.created_at >= period_start,
        )
        .group_by(UsageRecord.model_id)
    )
    models = [dict(r._mapping) for r in (await db.execute(model_query)).all()]

    run_limit = limits.get("runs_per_month")
    return {
        "plan": sub.plan,
        "period_start": period_start.isoformat(),
        "period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "prompt_tokens": row.prompt_tokens or 0,
        "completion_tokens": row.completion_tokens or 0,
        "cost_usd": float(row.cost_usd) if row.cost_usd else 0.0,
        "calls": row.calls or 0,
        "call_limit": run_limit,
        "models": models,
    }


# --- DB helpers -----------------------------------------------------------


async def get_or_create_subscription(
    db: AsyncSession, organization_id
) -> Subscription:
    stmt = select(Subscription).where(Subscription.organization_id == organization_id)
    sub = (await db.execute(stmt)).scalar_one_or_none()
    if sub is None:
        sub = Subscription(
            organization_id=organization_id,
            plan=PLAN_FREE,
            status=SUB_STATUS_ACTIVE,
            metadata_={},
        )
        db.add(sub)
        await db.flush()
    return sub


async def _ensure_stripe_customer(
    db: AsyncSession, *, organization: Organization, user: User
) -> str:
    """Return the Stripe customer ID for this org, creating one if needed."""
    sub = await get_or_create_subscription(db, organization.id)
    if sub.stripe_customer_id:
        return sub.stripe_customer_id
    stripe = _stripe_client()
    customer = stripe.Customer.create(
        email=user.email,
        name=organization.name,
        metadata={
            "organization_id": str(organization.id),
            "primary_user_id": str(user.id),
        },
    )
    sub.stripe_customer_id = customer["id"]
    await db.flush()
    return customer["id"]


# --- Public actions -------------------------------------------------------


async def create_checkout_session(
    db: AsyncSession,
    *,
    organization: Organization,
    user: User,
    plan: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Stripe Checkout session and return its hosted URL."""
    stripe = _stripe_client()

    price_id: str | None = None
    if plan == PLAN_STARTER:
        price_id = settings.stripe_price_starter
    elif plan == PLAN_PRO:
        price_id = settings.stripe_price_pro
    elif plan == PLAN_BUSINESS:
        price_id = settings.stripe_price_business

    if not price_id:
        raise BillingNotConfigured(
            f"No Stripe price ID configured for plan '{plan}'. "
            f"Set STRIPE_PRICE_{plan.upper()}."
        )

    customer_id = await _ensure_stripe_customer(
        db, organization=organization, user=user
    )

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        client_reference_id=str(organization.id),
        metadata={
            "organization_id": str(organization.id),
            "user_id": str(user.id),
            "plan": plan,
        },
        subscription_data={
            "metadata": {
                "organization_id": str(organization.id),
                "plan": plan,
            }
        },
    )
    return session["url"]


async def create_portal_session(
    db: AsyncSession,
    *,
    organization: Organization,
    user: User,
    return_url: str,
) -> str:
    """Create a Stripe Customer Portal session (manage payment + cancel)."""
    stripe = _stripe_client()
    customer_id = await _ensure_stripe_customer(
        db, organization=organization, user=user
    )
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session["url"]


# --- Webhook handling -----------------------------------------------------


def verify_webhook_signature(payload: bytes, signature: str) -> dict[str, Any]:
    """Parse + verify a Stripe webhook. Raises on bad signature."""
    if _stripe is None:
        raise BillingNotConfigured("stripe SDK not installed")
    if not settings.stripe_webhook_secret:
        raise BillingNotConfigured("STRIPE_WEBHOOK_SECRET is not set")
    return _stripe.Webhook.construct_event(
        payload=payload,
        sig_header=signature,
        secret=settings.stripe_webhook_secret,
    )


def _ts_to_dt(ts: int | None) -> datetime | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=UTC)


async def handle_webhook_event(db: AsyncSession, event: dict[str, Any]) -> None:
    """Process a verified Stripe event. Idempotent — replays are no-ops."""
    event_id = event.get("id")
    event_type = event.get("type", "")
    if not event_id:
        log.warning("billing.webhook.missing_id", event=event)
        return

    # Idempotency: skip if we've already recorded this event ID.
    existing = (
        await db.execute(
            select(BillingEvent.id).where(BillingEvent.stripe_event_id == event_id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        log.info("billing.webhook.duplicate", event_id=event_id)
        return

    data = event.get("data", {}).get("object", {}) or {}
    org_id = None

    if event_type.startswith("customer.subscription."):
        org_id = await _apply_subscription_event(db, event_type, data)
    elif event_type == "checkout.session.completed":
        org_id = await _apply_checkout_completed(db, data)
    elif event_type.startswith("invoice."):
        # Currently we just log; status comes from subscription events.
        log.info("billing.webhook.invoice", event_type=event_type)
    else:
        log.info("billing.webhook.unhandled", event_type=event_type)

    db.add(
        BillingEvent(
            stripe_event_id=event_id,
            event_type=event_type,
            organization_id=org_id,
            payload=event,
        )
    )
    await db.flush()


async def _apply_subscription_event(
    db: AsyncSession, event_type: str, sub_obj: dict[str, Any]
):
    org_id_str = (sub_obj.get("metadata") or {}).get("organization_id")
    if not org_id_str:
        log.warning(
            "billing.webhook.subscription_missing_org_id",
            sub_id=sub_obj.get("id"),
        )
        return None

    import uuid

    try:
        org_id = uuid.UUID(org_id_str)
    except (ValueError, TypeError):
        return None

    sub = await get_or_create_subscription(db, org_id)

    sub.stripe_subscription_id = sub_obj.get("id")
    sub.stripe_customer_id = sub_obj.get("customer") or sub.stripe_customer_id
    status = sub_obj.get("status", SUB_STATUS_ACTIVE)
    sub.status = status

    items = (sub_obj.get("items") or {}).get("data") or []
    price_id = items[0].get("price", {}).get("id") if items else None
    if price_id:
        sub.stripe_price_id = price_id
        sub.plan = plan_from_price_id(price_id)

    sub.current_period_end = _ts_to_dt(sub_obj.get("current_period_end"))
    sub.cancel_at_period_end = bool(sub_obj.get("cancel_at_period_end"))

    if event_type == "customer.subscription.deleted":
        sub.plan = PLAN_FREE
        sub.status = SUB_STATUS_CANCELED

    meta = dict(sub.metadata_ or {})
    meta["last_event_at"] = int(time.time())
    meta["last_event_type"] = event_type
    sub.metadata_ = meta

    await db.flush()
    return org_id


async def _apply_checkout_completed(db: AsyncSession, session_obj: dict[str, Any]):
    """When checkout completes, ensure the customer ID is stashed on the org."""
    import uuid

    org_id_str = session_obj.get("client_reference_id") or (
        session_obj.get("metadata") or {}
    ).get("organization_id")
    if not org_id_str:
        return None
    try:
        org_id = uuid.UUID(org_id_str)
    except (ValueError, TypeError):
        return None

    sub = await get_or_create_subscription(db, org_id)
    customer = session_obj.get("customer")
    if customer:
        sub.stripe_customer_id = customer
    await db.flush()
    return org_id
