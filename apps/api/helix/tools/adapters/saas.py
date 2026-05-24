"""SaaS tool adapters: Shopify, Klaviyo, Meta Ads, Stripe, Twilio, LinkedIn, YouTube, GA4.

All tools require valid credentials from tool_connections. No mock fallbacks.
Missing credentials = clear error response.
"""
from __future__ import annotations

import uuid
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.integrations.resolver import get_integration_credentials
from helix.tools.base import Tool, ToolResult

log = get_logger("helix.tools.saas")
settings = get_settings()


def _resolve_creds(session: Any, workspace_id: Any, provider: str) -> dict[str, str] | None:
    """Resolve credentials or return None."""
    if session is None or workspace_id is None:
        return None
    try:
        return get_integration_credentials(
            session, workspace_id=uuid.UUID(str(workspace_id)), provider=provider
        )
    except Exception:
        log.warning(f"{provider}_credentials_resolve_failed")
        return None


class ShopifyApiTool(Tool):
    name = "shopify_api"
    description = (
        "Interact with Shopify Admin API: get shop details, list/create products, "
        "list orders, and manage inventory."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        product_data: dict | None = None,
        limit: int = 10,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "shopify")
        if not creds:
            return ToolResult(ok=False, error="Shopify not connected. Go to Integrations > Shopify to connect your store.")

        token = creds.get("token") or creds.get("access_token")
        shop_domain = creds.get("shop_domain") or creds.get("extra", {}).get("shop_domain")
        if not token or not shop_domain:
            return ToolResult(ok=False, error="Shopify credentials incomplete. Reconnect your store.")

        api_version = settings.shopify_api_version or "2024-10"
        headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }
        base = f"https://{shop_domain}/admin/api/{api_version}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_shop":
                    r = await client.get(f"{base}/shop.json", headers=headers)
                elif op == "list_products":
                    r = await client.get(f"{base}/products.json?limit={limit}", headers=headers)
                elif op == "create_product":
                    if not product_data:
                        return ToolResult(ok=False, error="product_data required")
                    r = await client.post(f"{base}/products.json", headers=headers, json={"product": product_data})
                elif op == "list_orders":
                    r = await client.get(f"{base}/orders.json?limit={limit}", headers=headers)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Shopify error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("shopify_api_request_failed")
                return ToolResult(ok=False, error=f"Shopify communication failed: {exc}")


class KlaviyoApiTool(Tool):
    name = "klaviyo_api"
    description = (
        "Interact with Klaviyo API: list profiles, manage segments, create email marketing campaigns, "
        "and track flows or custom analytics."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        campaign_data: dict | None = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "klaviyo")
        if not creds:
            return ToolResult(ok=False, error="Klaviyo not connected. Go to Integrations > Klaviyo to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Klaviyo credentials incomplete. Reconnect your account.")

        api_revision = settings.klaviyo_api_revision or "2024-10-15"
        headers = {
            "Authorization": f"Klaviyo-API-Key {token}",
            "Accept": "application/json",
            "revision": api_revision,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "list_profiles":
                    r = await client.get("https://a.klaviyo.com/api/profiles/", headers=headers)
                elif op == "list_campaigns":
                    r = await client.get("https://a.klaviyo.com/api/campaigns/", headers=headers)
                elif op == "create_campaign":
                    if not campaign_data:
                        return ToolResult(ok=False, error="campaign_data required")
                    r = await client.post("https://a.klaviyo.com/api/campaigns/", headers=headers, json=campaign_data)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201, 202):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Klaviyo error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("klaviyo_api_request_failed")
                return ToolResult(ok=False, error=f"Klaviyo communication failed: {exc}")


class MetaAdsApiTool(Tool):
    name = "meta_ads_api"
    description = (
        "Interact with Meta Graph & Marketing API: manage ad accounts, create campaigns, "
        "set up target audiences and ad creatives, and fetch performance/ROAS analytics."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        campaign_name: str = "Helix Creative Ad Campaign",
        budget: float = 100.0,
        ad_creative_url: str | None = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "meta_ads")
        if not creds:
            return ToolResult(ok=False, error="Meta Ads not connected. Go to Integrations > Meta Ads to connect.")

        token = creds.get("token")
        ad_account_id = creds.get("ad_account_id")
        if not token or not ad_account_id:
            return ToolResult(ok=False, error="Meta Ads credentials incomplete. Reconnect your account.")

        api_version = settings.meta_graph_api_version or "v19.0"
        base = f"https://graph.facebook.com/{api_version}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_ad_account":
                    r = await client.get(f"{base}/{ad_account_id}?fields=name,account_status,currency&access_token={token}")
                elif op == "create_campaign":
                    r = await client.post(
                        f"{base}/{ad_account_id}/campaigns",
                        params={"access_token": token},
                        json={
                            "name": campaign_name,
                            "objective": "OUTCOME_SALES",
                            "status": "PAUSED",
                            "special_ad_categories": "[]"
                        }
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Meta error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("meta_ads_api_request_failed")
                return ToolResult(ok=False, error=f"Meta communication failed: {exc}")


class StripeApiTool(Tool):
    name = "stripe_api"
    description = (
        "Interact with Stripe Payment API: manage customers, list billing profiles, "
        "create checkout sessions, and get payment balance metrics."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        customer_email: str | None = None,
        amount_cents: int = 1000,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "stripe")
        if not creds:
            return ToolResult(ok=False, error="Stripe not connected. Go to Integrations > Stripe to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Stripe credentials incomplete. Reconnect your account.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_balance":
                    r = await client.get("https://api.stripe.com/v1/balance", headers=headers)
                elif op == "create_customer":
                    if not customer_email:
                        return ToolResult(ok=False, error="customer_email required")
                    r = await client.post("https://api.stripe.com/v1/customers", headers=headers, data={"email": customer_email})
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Stripe error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("stripe_api_request_failed")
                return ToolResult(ok=False, error=f"Stripe communication failed: {exc}")


class TwilioSmsTool(Tool):
    name = "twilio_sms"
    description = (
        "Send customer notifications, reservation alerts, and growth promotions "
        "via Twilio SMS or WhatsApp API."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        to: str = "+15550199",
        body: str = "Helix OS autonomous creative update!",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "twilio")
        if not creds:
            return ToolResult(ok=False, error="Twilio not connected. Go to Integrations > Twilio to connect.")

        account_sid = creds.get("account_sid") or creds.get("token")
        auth_token = creds.get("auth_token")
        if not account_sid or not auth_token:
            return ToolResult(ok=False, error="Twilio credentials incomplete. Reconnect your account.")

        auth = (account_sid, auth_token)
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "send_sms":
                    r = await client.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                        auth=auth,
                        data={"To": to, "From": "+18885550199", "Body": body},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Twilio error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("twilio_api_request_failed")
                return ToolResult(ok=False, error=f"Twilio communication failed: {exc}")


class LinkedInApiTool(Tool):
    name = "linkedin_api"
    description = (
        "Interact with LinkedIn API: post company updates, manage ad campaigns, "
        "and fetch company page analytics."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        text: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "linkedin")
        if not creds:
            return ToolResult(ok=False, error="LinkedIn not connected. Go to Integrations > LinkedIn to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="LinkedIn credentials incomplete. Reconnect your account.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-Restli-Protocol-Version": "2.0.0"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_profile":
                    r = await client.get("https://api.linkedin.com/v2/me", headers=headers)
                elif op == "share_post":
                    if not text:
                        return ToolResult(ok=False, error="text required")
                    payload = {"author": "urn:li:person:me", "lifecycleState": "PUBLISHED", "specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}}, "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}}
                    r = await client.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"LinkedIn error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("linkedin_api_request_failed")
                return ToolResult(ok=False, error=f"LinkedIn communication failed: {exc}")


class YouTubeApiTool(Tool):
    name = "youtube_api"
    description = (
        "Interact with YouTube Data API: upload videos, manage playlists, "
        "and fetch channel analytics."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "youtube")
        if not creds:
            return ToolResult(ok=False, error="YouTube not connected. Go to Integrations > YouTube to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="YouTube credentials incomplete. Reconnect your account.")

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_channel":
                    r = await client.get("https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true", headers=headers)
                elif op == "list_videos":
                    r = await client.get("https://www.googleapis.com/youtube/v3/search?part=snippet&forMine=true&type=video&maxResults=10", headers=headers)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"YouTube error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("youtube_api_request_failed")
                return ToolResult(ok=False, error=f"YouTube communication failed: {exc}")


class Ga4ApiTool(Tool):
    name = "ga4_api"
    description = (
        "Interact with Google Analytics 4 Data API: run reports, fetch audience metrics, "
        "and get conversion data."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        property_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "ga4")
        if not creds:
            return ToolResult(ok=False, error="GA4 not connected. Go to Integrations > GA4 to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="GA4 credentials incomplete. Reconnect your account.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "run_report":
                    if not property_id:
                        return ToolResult(ok=False, error="property_id required")
                    payload = {
                        "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
                        "metrics": [{"name": "sessions"}, {"name": "activeUsers"}, {"name": "conversions"}],
                    }
                    r = await client.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport", headers=headers, json=payload)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"GA4 error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("ga4_api_request_failed")
                return ToolResult(ok=False, error=f"GA4 communication failed: {exc}")


class WooCommerceApiTool(Tool):
    name = "woocommerce_api"
    description = (
        "Interact with WooCommerce REST API: list products, orders, customers, "
        "and create coupons."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        product_data: dict | None = None,
        limit: int = 10,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "woocommerce")
        if not creds:
            return ToolResult(ok=False, error="WooCommerce not connected. Go to Integrations > WooCommerce to connect.")

        consumer_key = creds.get("consumer_key")
        consumer_secret = creds.get("consumer_secret")
        store_url = creds.get("store_url")
        if not consumer_key or not consumer_secret or not store_url:
            return ToolResult(ok=False, error="WooCommerce credentials incomplete. Reconnect your store.")

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "list_products":
                    r = await client.get(f"{store_url}/wp-json/wc/v3/products?per_page={limit}", auth=(consumer_key, consumer_secret))
                elif op == "create_product":
                    if not product_data:
                        return ToolResult(ok=False, error="product_data required")
                    r = await client.post(f"{store_url}/wp-json/wc/v3/products", auth=(consumer_key, consumer_secret), json=product_data)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"WooCommerce error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("woocommerce_api_request_failed")
                return ToolResult(ok=False, error=f"WooCommerce communication failed: {exc}")
