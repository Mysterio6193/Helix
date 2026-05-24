"""Restaurant/POS tool adapters: Toast, Square, DoorDash, UberEats, Yelp.

All tools require valid credentials from tool_connections. No mock fallbacks.
"""
from __future__ import annotations

import uuid
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.integrations.resolver import get_integration_credentials
from helix.tools.base import Tool, ToolResult

log = get_logger("helix.tools.restaurant")
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


class ToastApiTool(Tool):
    name = "toast_api"
    description = (
        "Interact with Toast POS API: get menu items, list orders, "
        "and fetch sales data."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "toast")
        if not creds:
            return ToolResult(ok=False, error="Toast not connected. Go to Integrations > Toast to connect.")

        client_secret = creds.get("token")
        if not client_secret:
            return ToolResult(ok=False, error="Toast API client secret required.")

        headers = {
            "Authorization": f"Bearer {client_secret}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_menu":
                    r = await client.get(
                        "https://api.toasttab.com/menus/v2/menus",
                        headers=headers,
                    )
                elif op == "list_orders":
                    r = await client.get(
                        "https://api.toasttab.com/orders/v2/orders",
                        headers=headers,
                        params={"pageSize": 50},
                    )
                elif op == "get_sales":
                    r = await client.get(
                        "https://api.toasttab.com/cashmgmt/v1/sales",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Toast error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("toast_api_request_failed")
                return ToolResult(ok=False, error=f"Toast communication failed: {exc}")


class SquareApiTool(Tool):
    name = "square_api"
    description = (
        "Interact with Square API: list items, get payments, "
        "create orders, and manage inventory."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "square")
        if not creds:
            return ToolResult(ok=False, error="Square not connected. Go to Integrations > Square to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Square access token required.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "list_items":
                    r = await client.get(
                        f"{settings.square_api_base.rstrip('/')}/v2/catalog/list",
                        headers=headers,
                    )
                elif op == "get_payments":
                    r = await client.get(
                        f"{settings.square_api_base.rstrip('/')}/v2/payments",
                        headers=headers,
                        params={"limit": 50},
                    )
                elif op == "create_order":
                    r = await client.post(
                        f"{settings.square_api_base.rstrip('/')}/v2/orders",
                        headers=headers,
                        json={"order": {"location_id": "main"}},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Square error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("square_api_request_failed")
                return ToolResult(ok=False, error=f"Square communication failed: {exc}")


class DoorDashApiTool(Tool):
    name = "doordash_api"
    description = (
        "Interact with DoorDash Drive API: create deliveries, "
        "get delivery status, and list stores."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "doordash")
        if not creds:
            return ToolResult(ok=False, error="DoorDash not connected. Go to Integrations > DoorDash to connect.")

        jwt_secret = creds.get("token")
        if not jwt_secret:
            return ToolResult(ok=False, error="DoorDash JWT signing secret required.")

        headers = {
            "Authorization": f"Bearer {jwt_secret}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "list_stores":
                    r = await client.get(
                        "https://developer.doordash.com/api/v2/stores",
                        headers=headers,
                    )
                elif op == "create_delivery":
                    r = await client.post(
                        "https://developer.doordash.com/api/v2/deliveries",
                        headers=headers,
                        json={
                            "external_delivery_id": "helix-delivery-001",
                            "pickup_address": "123 Main St",
                            "dropoff_address": "456 Oak Ave",
                        },
                    )
                elif op == "get_status":
                    r = await client.get(
                        "https://developer.doordash.com/api/v2/deliveries/helix-delivery-001",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"DoorDash error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("doordash_api_request_failed")
                return ToolResult(ok=False, error=f"DoorDash communication failed: {exc}")


class UberEatsApiTool(Tool):
    name = "ubereats_api"
    description = (
        "Interact with Uber Eats API: get orders, update menu, "
        "and get store information."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        store_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "ubereats")
        if not creds:
            return ToolResult(ok=False, error="UberEats not connected. Go to Integrations > UberEats to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="UberEats OAuth access token required.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_orders":
                    r = await client.get(
                        "https://api.uber.com/v1/eats/orders",
                        headers=headers,
                    )
                elif op == "get_store":
                    if not store_id:
                        return ToolResult(ok=False, error="store_id required")
                    r = await client.get(
                        f"https://api.uber.com/v1/eats/stores/{store_id}",
                        headers=headers,
                    )
                elif op == "update_menu":
                    if not store_id:
                        return ToolResult(ok=False, error="store_id required")
                    r = await client.post(
                        f"https://api.uber.com/v1/eats/stores/{store_id}/menu",
                        headers=headers,
                        json={"items": []},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"UberEats error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("ubereats_api_request_failed")
                return ToolResult(ok=False, error=f"UberEats communication failed: {exc}")


class YelpApiTool(Tool):
    name = "yelp_api"
    description = (
        "Interact with Yelp Fusion API: get business info, "
        "search businesses, and get reviews."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        business_id: str = "",
        term: str = "",
        location: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "yelp")
        if not creds:
            return ToolResult(ok=False, error="Yelp not connected. Go to Integrations > Yelp to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Yelp Fusion API key required.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_business":
                    if not business_id:
                        return ToolResult(ok=False, error="business_id required")
                    r = await client.get(
                        f"{settings.yelp_api_base.rstrip('/')}/v3/businesses/{business_id}",
                        headers=headers,
                    )
                elif op == "search":
                    if not term or not location:
                        return ToolResult(ok=False, error="term and location required")
                    r = await client.get(
                        f"{settings.yelp_api_base.rstrip('/')}/v3/businesses/search",
                        headers=headers,
                        params={"term": term, "location": location, "limit": 10},
                    )
                elif op == "get_reviews":
                    if not business_id:
                        return ToolResult(ok=False, error="business_id required")
                    r = await client.get(
                        f"{settings.yelp_api_base.rstrip('/')}/v3/businesses/{business_id}/reviews",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Yelp error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("yelp_api_request_failed")
                return ToolResult(ok=False, error=f"Yelp communication failed: {exc}")
