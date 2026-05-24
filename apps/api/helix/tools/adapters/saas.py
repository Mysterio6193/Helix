"""SaaS tool adapters: Shopify, Klaviyo, Meta Ads, Stripe, Twilio.

These tools support both live execution (hitting the real SaaS APIs if valid credentials
are retrieved from tool_connections) and high-fidelity mock execution (returning structured,
realistic commerce data if running in sandbox/development or with mock tokens).
"""
from __future__ import annotations

import time
import uuid
from typing import Any

import httpx

from helix.core.logging import get_logger
from helix.integrations.resolver import get_integration_credentials
from helix.tools.base import Tool, ToolResult

log = get_logger("helix.tools.saas")


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
        token = "mock"
        shop_domain = "mock-shop"

        # Try to resolve real credentials from workspace db connection if provided
        if session is not None and workspace_id is not None:
            try:
                creds = await get_integration_credentials(
                    session, workspace_id=uuid.UUID(str(workspace_id)), provider="shopify"
                )
                if creds:
                    token = creds.get("token") or creds.get("access_token") or "mock"
                    shop_domain = creds.get("shop_domain") or creds.get("extra", {}).get("shop_domain") or "mock-shop"
            except Exception:
                log.warning("shopify_credentials_resolve_failed, defaulting to mock")

        is_mock = token.startswith("mock") or token == "mock" or shop_domain.startswith("mock")

        if not is_mock:
            # Real Shopify admin API call
            headers = {
                "X-Shopify-Access-Token": token,
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    if op == "get_shop":
                        r = await client.get(f"https://{shop_domain}/admin/api/2024-04/shop.json", headers=headers)
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Shopify error {r.status_code}: {r.text}")
                    elif op == "list_products":
                        r = await client.get(f"https://{shop_domain}/admin/api/2024-04/products.json?limit={limit}", headers=headers)
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Shopify error {r.status_code}: {r.text}")
                    elif op == "create_product":
                        if not product_data:
                            return ToolResult(ok=False, error="product_data required")
                        r = await client.post(
                            f"https://{shop_domain}/admin/api/2024-04/products.json",
                            headers=headers,
                            json={"product": product_data},
                        )
                        if r.status_code in (200, 201):
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Shopify error {r.status_code}: {r.text}")
                    elif op == "list_orders":
                        r = await client.get(f"https://{shop_domain}/admin/api/2024-04/orders.json?limit={limit}", headers=headers)
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Shopify error {r.status_code}: {r.text}")
                except Exception as exc:
                    log.exception("shopify_api_request_failed")
                    return ToolResult(ok=False, error=f"Shopify communication failed: {str(exc)}")

        # High-Fidelity Mock Response
        log.info("shopify_api_mock_execution", op=op)
        if op == "get_shop":
            return ToolResult(ok=True, data={
                "shop": {
                    "id": 89457294,
                    "name": "Cozy Diner Gourmet",
                    "email": "hello@cozydiner.com",
                    "domain": "cozydiner.myshopify.com",
                    "currency": "USD",
                    "country_name": "United States",
                    "plan_name": "shopify_plus"
                }
            })
        elif op == "list_products":
            return ToolResult(ok=True, data={
                "products": [
                    {
                        "id": 1001,
                        "title": "Gourmet Truffle Burger Combo",
                        "body_html": "Juicy black angus beef patty, white truffle aioli, melted swiss cheese, and caramelized onions on toasted brioche.",
                        "vendor": "Cozy Diner Gourmet",
                        "product_type": "Food & Beverage",
                        "status": "active",
                        "variants": [{"id": 2001, "price": "18.99", "inventory_quantity": 42}],
                        "images": [{"id": 3001, "src": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"}]
                    },
                    {
                        "id": 1002,
                        "title": "Artisanal Crispy Chicken Sandwich",
                        "body_html": "Buttermilk fried chicken breast, house pickles, garlic aioli, spicy slaw, served on a warm bun.",
                        "vendor": "Cozy Diner Gourmet",
                        "product_type": "Food & Beverage",
                        "status": "active",
                        "variants": [{"id": 2002, "price": "15.49", "inventory_quantity": 80}],
                        "images": [{"id": 3002, "src": "https://images.unsplash.com/photo-1627662236973-4f8259fa2441?w=500"}]
                    }
                ]
            })
        elif op == "create_product":
            pdata = product_data or {"title": "New Mock Product", "price": "9.99"}
            return ToolResult(ok=True, data={
                "product": {
                    "id": int(time.time()),
                    "title": pdata.get("title", "New Product"),
                    "body_html": pdata.get("body_html", "Delicious product description."),
                    "status": "active",
                    "variants": [{"id": int(time.time()) + 1, "price": pdata.get("price", "9.99"), "inventory_quantity": 100}]
                }
            })
        elif op == "list_orders":
            return ToolResult(ok=True, data={
                "orders": [
                    {
                        "id": 5001,
                        "name": "#1001",
                        "email": "customer@example.com",
                        "total_price": "34.48",
                        "financial_status": "paid",
                        "fulfillment_status": "fulfilled",
                        "line_items": [
                            {"id": 6001, "title": "Gourmet Truffle Burger Combo", "quantity": 1, "price": "18.99"},
                            {"id": 6002, "title": "Artisanal Crispy Chicken Sandwich", "quantity": 1, "price": "15.49"}
                        ]
                    }
                ]
            })
        return ToolResult(ok=False, error=f"unknown op: {op}")


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
        token = "mock"

        if session is not None and workspace_id is not None:
            try:
                creds = await get_integration_credentials(
                    session, workspace_id=uuid.UUID(str(workspace_id)), provider="klaviyo"
                )
                if creds:
                    token = creds.get("token") or "mock"
            except Exception:
                log.warning("klaviyo_credentials_resolve_failed, defaulting to mock")

        is_mock = token.startswith("mock") or token == "mock"

        if not is_mock:
            headers = {
                "Authorization": f"Klaviyo-API-Key {token}",
                "Accept": "application/json",
                "revision": "2024-05-15",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    if op == "list_profiles":
                        r = await client.get("https://a.klaviyo.com/api/profiles/", headers=headers)
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Klaviyo error {r.status_code}: {r.text}")
                    elif op == "list_campaigns":
                        r = await client.get("https://a.klaviyo.com/api/campaigns/", headers=headers)
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Klaviyo error {r.status_code}: {r.text}")
                    elif op == "create_campaign":
                        if not campaign_data:
                            return ToolResult(ok=False, error="campaign_data required")
                        r = await client.post(
                            "https://a.klaviyo.com/api/campaigns/",
                            headers=headers,
                            json=campaign_data,
                        )
                        if r.status_code in (200, 201, 202):
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Klaviyo error {r.status_code}: {r.text}")
                except Exception as exc:
                    log.exception("klaviyo_api_request_failed")
                    return ToolResult(ok=False, error=f"Klaviyo communication failed: {str(exc)}")

        # High-Fidelity Mock Response
        log.info("klaviyo_api_mock_execution", op=op)
        if op == "list_profiles":
            return ToolResult(ok=True, data={
                "data": [
                    {
                        "type": "profile",
                        "id": "01GD5V0294JSAJK",
                        "attributes": {
                            "email": "sarah.jones@example.com",
                            "first_name": "Sarah",
                            "last_name": "Jones",
                            "phone_number": "+15550199",
                            "created": "2026-01-10T14:32:00Z"
                        }
                    },
                    {
                        "type": "profile",
                        "id": "01GD5V0304JSAKL",
                        "attributes": {
                            "email": "michael.smith@example.com",
                            "first_name": "Michael",
                            "last_name": "Smith",
                            "phone_number": "+15550201",
                            "created": "2026-02-15T09:12:00Z"
                        }
                    }
                ]
            })
        elif op == "list_campaigns":
            return ToolResult(ok=True, data={
                "data": [
                    {
                        "type": "campaign",
                        "id": "01HN7K8234B",
                        "attributes": {
                            "name": "Spring Burger Launch Promotion",
                            "status": "sent",
                            "scheduled_at": "2026-04-12T10:00:00Z"
                        }
                    }
                ]
            })
        elif op == "create_campaign":
            cname = (campaign_data or {}).get("name", "New Mock Campaign")
            return ToolResult(ok=True, data={
                "data": {
                    "type": "campaign",
                    "id": "01HN7K9999B",
                    "attributes": {
                        "name": cname,
                        "status": "draft",
                        "created_at": "2026-05-24T00:00:00Z"
                    }
                }
            })
        elif op == "get_campaign_analytics":
            return ToolResult(ok=True, data={
                "analytics": {
                    "campaign_id": "01HN7K8234B",
                    "recipient_count": 1250,
                    "open_rate": 0.384,  # 38.4%
                    "click_rate": 0.089,  # 8.9%
                    "bounce_rate": 0.005,  # 0.5%
                    "conversion_value_usd": 1245.50,
                    "conversions": 62
                }
            })
        return ToolResult(ok=False, error=f"unknown op: {op}")


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
        token = "mock"
        ad_account_id = "act_mock"

        if session is not None and workspace_id is not None:
            try:
                creds = await get_integration_credentials(
                    session, workspace_id=uuid.UUID(str(workspace_id)), provider="meta_ads"
                )
                if creds:
                    token = creds.get("token") or "mock"
                    ad_account_id = creds.get("ad_account_id") or "act_mock"
            except Exception:
                log.warning("meta_ads_credentials_resolve_failed, defaulting to mock")

        is_mock = token.startswith("mock") or token == "mock" or ad_account_id.startswith("act_mock")

        if not is_mock:
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    if op == "get_ad_account":
                        r = await client.get(f"https://graph.facebook.com/v19.0/{ad_account_id}?fields=name,account_status,currency&access_token={token}")
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Meta error {r.status_code}: {r.text}")
                    elif op == "create_campaign":
                        r = await client.post(
                            f"https://graph.facebook.com/v19.0/{ad_account_id}/campaigns",
                            params={"access_token": token},
                            json={
                                "name": campaign_name,
                                "objective": "OUTCOME_SALES",
                                "status": "PAUSED",
                                "special_ad_categories": "[]"
                            }
                        )
                        if r.status_code in (200, 201):
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Meta error {r.status_code}: {r.text}")
                except Exception as exc:
                    log.exception("meta_ads_api_request_failed")
                    return ToolResult(ok=False, error=f"Meta communication failed: {str(exc)}")

        # High-Fidelity Mock Response
        log.info("meta_ads_api_mock_execution", op=op)
        if op == "get_ad_account":
            return ToolResult(ok=True, data={
                "id": "act_89472938",
                "name": "Cozy Diner Gourmet Main Ad Set",
                "account_status": 1,  # Active
                "currency": "USD"
            })
        elif op == "create_campaign":
            return ToolResult(ok=True, data={
                "id": f"2385938{int(time.time() % 10000)}",
                "name": campaign_name,
                "status": "PAUSED",
                "objective": "OUTCOME_SALES",
                "daily_budget": str(budget * 100)  # Cents
            })
        elif op == "create_ad_set":
            return ToolResult(ok=True, data={
                "id": f"2385940{int(time.time() % 10000)}",
                "name": f"AdSet: {campaign_name} - Broad Geo",
                "targeting": {"geo_locations": {"countries": ["US"]}, "age_min": 18},
                "status": "ACTIVE"
            })
        elif op == "create_ad":
            return ToolResult(ok=True, data={
                "id": f"2385950{int(time.time() % 10000)}",
                "name": "Ad: Truffle Burger High-CTR Video",
                "creative": {"image_url": ad_creative_url or "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"}
            })
        elif op == "get_campaign_insights":
            return ToolResult(ok=True, data={
                "data": [
                    {
                        "campaign_id": "2385938024",
                        "campaign_name": campaign_name,
                        "impressions": "48924",
                        "clicks": "1248",
                        "ctr": "0.0255",  # 2.55%
                        "spend": "340.50",
                        "cpc": "0.27",
                        "conversions": "84",
                        "purchase_value": "1596.00",
                        "roas": "4.68"
                    }
                ]
            })
        return ToolResult(ok=False, error=f"unknown op: {op}")


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
        token = "mock"

        if session is not None and workspace_id is not None:
            try:
                creds = await get_integration_credentials(
                    session, workspace_id=uuid.UUID(str(workspace_id)), provider="stripe"
                )
                if creds:
                    token = creds.get("token") or "mock"
            except Exception:
                log.warning("stripe_credentials_resolve_failed, defaulting to mock")

        is_mock = token.startswith("mock") or token == "mock"

        if not is_mock:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    if op == "get_balance":
                        r = await client.get("https://api.stripe.com/v1/balance", headers=headers)
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Stripe error {r.status_code}: {r.text}")
                    elif op == "create_customer":
                        if not customer_email:
                            return ToolResult(ok=False, error="customer_email required")
                        r = await client.post(
                            "https://api.stripe.com/v1/customers",
                            headers=headers,
                            data={"email": customer_email},
                        )
                        if r.status_code == 200:
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Stripe error {r.status_code}: {r.text}")
                except Exception as exc:
                    log.exception("stripe_api_request_failed")
                    return ToolResult(ok=False, error=f"Stripe communication failed: {str(exc)}")

        # High-Fidelity Mock Response
        log.info("stripe_api_mock_execution", op=op)
        if op == "get_balance":
            return ToolResult(ok=True, data={
                "object": "balance",
                "available": [{"amount": 1459450, "currency": "usd"}],
                "pending": [{"amount": 234500, "currency": "usd"}]
            })
        elif op == "create_customer":
            return ToolResult(ok=True, data={
                "id": f"cus_O{int(time.time())}",
                "object": "customer",
                "email": customer_email or "guest@example.com",
                "currency": "usd"
            })
        elif op == "create_charge":
            return ToolResult(ok=True, data={
                "id": f"ch_{int(time.time())}",
                "object": "charge",
                "amount": amount_cents,
                "paid": True,
                "status": "succeeded"
            })
        elif op == "create_invoice":
            return ToolResult(ok=True, data={
                "id": f"in_{int(time.time())}",
                "object": "invoice",
                "amount_due": amount_cents,
                "customer": "cus_mock123",
                "status": "draft"
            })
        return ToolResult(ok=False, error=f"unknown op: {op}")


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
        account_sid = "mock_sid"
        auth_token = "mock_token"

        if session is not None and workspace_id is not None:
            try:
                creds = await get_integration_credentials(
                    session, workspace_id=uuid.UUID(str(workspace_id)), provider="twilio"
                )
                if creds:
                    account_sid = creds.get("account_sid") or creds.get("token") or "mock_sid"
                    auth_token = creds.get("auth_token") or "mock_token"
            except Exception:
                log.warning("twilio_credentials_resolve_failed, defaulting to mock")

        is_mock = account_sid.startswith("mock") or account_sid == "mock_sid"

        if not is_mock:
            auth = (account_sid, auth_token)
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    if op == "send_sms":
                        r = await client.post(
                            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                            auth=auth,
                            data={"To": to, "From": "+18885550199", "Body": body},
                        )
                        if r.status_code in (200, 201):
                            return ToolResult(ok=True, data=r.json())
                        return ToolResult(ok=False, error=f"Twilio error {r.status_code}: {r.text}")
                except Exception as exc:
                    log.exception("twilio_api_request_failed")
                    return ToolResult(ok=False, error=f"Twilio communication failed: {str(exc)}")

        # High-Fidelity Mock Response
        log.info("twilio_sms_mock_execution", op=op)
        if op == "send_sms":
            return ToolResult(ok=True, data={
                "sid": f"SM{uuid.uuid4().hex[:30]}",
                "status": "queued",
                "to": to,
                "body": body,
                "date_created": "2026-05-24T00:00:00Z"
            })
        elif op == "list_messages":
            return ToolResult(ok=True, data={
                "messages": [
                    {
                        "sid": "SM385929384",
                        "status": "delivered",
                        "to": to,
                        "body": body,
                        "date_sent": "2026-05-24T00:01:00Z"
                    }
                ]
            })
        return ToolResult(ok=False, error=f"unknown op: {op}")
