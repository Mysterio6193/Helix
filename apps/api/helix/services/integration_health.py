"""Integration health monitoring service.

Periodically validates all connected integration tokens and updates health status.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.models.tool_connection import ToolConnection

log = get_logger("helix.services.integration_health")
settings = get_settings()

# Lightweight verification endpoints for each provider
HEALTH_CHECKS: dict[str, dict[str, Any]] = {
    "telegram": {"method": "GET", "url": "{token}/getMe", "base": "telegram_api_base", "bot_prefix": True},
    "slack": {"method": "GET", "url": "/auth.test", "base": "slack_api_base", "auth_header": True},
    "discord": {"method": "GET", "url": "https://discord.com/api/v10/users/@me", "auth_header": True, "bot_prefix": True},
    "stripe": {"method": "GET", "url": "/v1/account", "base": "stripe_api_base", "basic_auth": True},
    "shopify": {"method": "GET", "url": "/shop.json", "requires_domain": True},
    "mailchimp": {"method": "GET", "url": "/3.0/lists", "requires_datacenter": True},
    "hubspot": {"method": "GET", "url": "https://api.hubapi.com/integrations/v1/me", "auth_header": True},
    "airtable": {"method": "GET", "url": "/v0/meta/whoami", "base": "airtable_api_base", "auth_header": True},
    "linear": {"method": "POST", "url": "https://api.linear.app/graphql", "auth_header": True, "body": {"query": "{ viewer { id } }"}},
    "sendgrid": {"method": "GET", "url": "/v3/user/account", "base": "sendgrid_api_base", "auth_header": True},
    "meta_ads": {"method": "GET", "url": "https://graph.facebook.com/v19.0/me", "query_param": "access_token"},
    "twitter": {"method": "GET", "url": "https://api.twitter.com/2/users/me", "auth_header": True},
    "yelp": {"method": "GET", "url": "https://api.yelp.com/v3/businesses/search", "auth_header": True, "query": {"term": "test", "location": "NYC", "limit": 1}},
}


async def check_provider_health(
    provider: str,
    token: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check if a provider token is valid by making a lightweight API call."""
    check = HEALTH_CHECKS.get(provider)
    if not check:
        return {"status": "unknown", "message": "No health check configured"}

    extra = extra or {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            method = check["method"]
            url = check["url"]
            headers = {}
            params = check.get("query", {})
            json_body = check.get("body")
            auth = None

            # Build URL
            if "base" in check:
                base = getattr(settings, check["base"], "")
                url = f"{base.rstrip('/')}{url}"
            elif check.get("requires_domain"):
                domain = extra.get("shop_domain", "")
                if not domain:
                    return {"status": "error", "message": "shop_domain required"}
                api_version = settings.shopify_api_version or "2024-10"
                url = f"https://{domain}/admin/api/{api_version}{url}"
            elif check.get("requires_datacenter"):
                dc = token.split("-")[-1] if "-" in token else "us1"
                url = f"https://{dc}.api.mailchimp.com{url}"
            elif check.get("bot_prefix") and provider == "telegram":
                url = f"{settings.telegram_api_base.rstrip('/')}/bot{url}"

            # Auth
            if check.get("auth_header"):
                if check.get("bot_prefix") and provider == "discord":
                    headers["Authorization"] = f"Bot {token}"
                else:
                    headers["Authorization"] = f"Bearer {token}"
            elif check.get("basic_auth"):
                auth = (token, "")
            elif check.get("query_param"):
                params[check["query_param"]] = token

            if method == "GET":
                r = await client.get(url, headers=headers, params=params, auth=auth)
            elif method == "POST":
                r = await client.post(url, headers=headers, json=json_body, auth=auth)
            else:
                return {"status": "unknown", "message": "Unsupported method"}

            if r.status_code in (200, 201):
                return {"status": "healthy", "status_code": r.status_code}
            elif r.status_code == 401:
                return {"status": "expired", "status_code": r.status_code, "message": "Token invalid or expired"}
            else:
                return {"status": "error", "status_code": r.status_code, "message": r.text[:200]}
    except Exception as exc:
        log.warning("health_check_failed", provider=provider, error=str(exc))
        return {"status": "unreachable", "message": str(exc)}


async def run_health_checks(db: AsyncSession) -> dict[str, Any]:
    """Run health checks on all enabled connections and update their status."""
    stmt = select(ToolConnection).where(ToolConnection.enabled.is_(True))
    rows = (await db.execute(stmt)).scalars().all()

    import json

    from helix.core.security import decrypt

    results = []
    healthy_count = 0
    expired_count = 0
    error_count = 0

    for conn in rows:
        try:
            creds = json.loads(decrypt(conn.credentials_encrypted))
            token = creds.get("token") or creds.get("access_token", "")
            if not token:
                continue

            health = await check_provider_health(conn.provider, token, creds)

            # Update connection metadata
            metadata = conn.metadata or {}
            metadata["last_health_check"] = datetime.now(UTC).isoformat()
            metadata["health_status"] = health["status"]
            if health.get("message"):
                metadata["health_error"] = health["message"]
            conn.metadata = metadata

            if health["status"] == "healthy":
                healthy_count += 1
            elif health["status"] == "expired":
                expired_count += 1
            else:
                error_count += 1

            results.append({
                "provider": conn.provider,
                "account_label": conn.account_label,
                "status": health["status"],
                "message": health.get("message"),
            })
        except Exception as exc:
            log.warning("health_check_connection_failed", provider=conn.provider, error=str(exc))
            error_count += 1
            results.append({
                "provider": conn.provider,
                "account_label": conn.account_label,
                "status": "error",
                "message": str(exc),
            })

    await db.commit()

    return {
        "checked": len(rows),
        "healthy": healthy_count,
        "expired": expired_count,
        "error": error_count,
        "results": results,
        "checked_at": datetime.now(UTC).isoformat(),
    }