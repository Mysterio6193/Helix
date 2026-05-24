"""POS system tool adapters: Petpooja, Clover, Lightspeed, Revel, ChowNow, Ordermark, Slice.

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

log = get_logger("helix.tools.pos")
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


class PetpoojaApiTool(Tool):
    name = "petpooja_api"
    description = (
        "Interact with Petpooja POS API: get menu items, list orders, "
        "get customers, and fetch billing data."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "petpooja")
        if not creds:
            return ToolResult(
                ok=False,
                error="Petpooja not connected. "
                "Go to Integrations > Petpooja to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Petpooja API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        base = "https://api.petpooja.com/v1"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_menu":
                    r = await client.get(f"{base}/menu", headers=headers)
                elif op == "list_orders":
                    r = await client.get(f"{base}/orders", headers=headers)
                elif op == "get_customers":
                    r = await client.get(f"{base}/customers", headers=headers)
                elif op == "get_billing":
                    r = await client.get(f"{base}/billing", headers=headers)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Petpooja error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("petpooja_api_request_failed")
                return ToolResult(ok=False, error=f"Petpooja communication failed: {exc}")


class CloverApiTool(Tool):
    name = "clover_api"
    description = (
        "Interact with Clover POS API: get merchant info, list orders, "
        "get items, and fetch payments."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        merchant_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "clover")
        if not creds:
            return ToolResult(
                ok=False,
                error="Clover not connected. Go to Integrations > Clover to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Clover API token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        mid = merchant_id or creds.get("merchant_id", "")
        if not mid:
            return ToolResult(ok=False, error="merchant_id required")

        base = f"https://api.clover.com/v3/merchants/{mid}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_merchant":
                    r = await client.get(f"{base}", headers=headers)
                elif op == "list_orders":
                    r = await client.get(f"{base}/orders", headers=headers)
                elif op == "get_items":
                    r = await client.get(f"{base}/items", headers=headers)
                elif op == "get_payments":
                    r = await client.get(f"{base}/payments", headers=headers)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Clover error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("clover_api_request_failed")
                return ToolResult(ok=False, error=f"Clover communication failed: {exc}")


class LightspeedApiTool(Tool):
    name = "lightspeed_api"
    description = (
        "Interact with Lightspeed POS API: get account info, list sales, "
        "get products, and fetch customers."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        account_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "lightspeed")
        if not creds:
            return ToolResult(
                ok=False,
                error="Lightspeed not connected. "
                "Go to Integrations > Lightspeed to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Lightspeed API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        aid = account_id or creds.get("account_id", "")

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_account":
                    r = await client.get(
                        "https://api.lightspeedapp.com/API/Account.json",
                        headers=headers,
                    )
                elif op == "list_sales":
                    if not aid:
                        return ToolResult(ok=False, error="account_id required")
                    r = await client.get(
                        f"https://api.lightspeedapp.com/API/{aid}/Sale.json",
                        headers=headers,
                    )
                elif op == "get_products":
                    if not aid:
                        return ToolResult(ok=False, error="account_id required")
                    r = await client.get(
                        f"https://api.lightspeedapp.com/API/{aid}/Item.json",
                        headers=headers,
                    )
                elif op == "get_customers":
                    if not aid:
                        return ToolResult(ok=False, error="account_id required")
                    r = await client.get(
                        f"https://api.lightspeedapp.com/API/{aid}/Customer.json",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Lightspeed error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("lightspeed_api_request_failed")
                return ToolResult(ok=False, error=f"Lightspeed communication failed: {exc}")


class RevelApiTool(Tool):
    name = "revel_api"
    description = (
        "Interact with Revel Systems API: get orders, list products, "
        "get customers, and fetch reports."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "revel")
        if not creds:
            return ToolResult(
                ok=False,
                error="Revel not connected. Go to Integrations > Revel to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Revel API key required.")

        headers = {"API-AUTHENTICATION": token, "Content-Type": "application/json"}
        base = "https://revel.revelup.com/resources"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_orders":
                    r = await client.get(f"{base}/Order", headers=headers)
                elif op == "get_products":
                    r = await client.get(f"{base}/Product", headers=headers)
                elif op == "get_customers":
                    r = await client.get(f"{base}/Customer", headers=headers)
                elif op == "get_establishment":
                    r = await client.get(f"{base}/Establishment", headers=headers)
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Revel error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("revel_api_request_failed")
                return ToolResult(ok=False, error=f"Revel communication failed: {exc}")


class ChowNowApiTool(Tool):
    name = "chownow_api"
    description = (
        "Interact with ChowNow API: get restaurants, list orders, "
        "and get menu data."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        restaurant_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "chownow")
        if not creds:
            return ToolResult(
                ok=False,
                error="ChowNow not connected. "
                "Go to Integrations > ChowNow to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="ChowNow API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_restaurants":
                    r = await client.get(
                        "https://api.chownow.com/v1/restaurants",
                        headers=headers,
                    )
                elif op == "get_orders":
                    if not restaurant_id:
                        return ToolResult(ok=False, error="restaurant_id required")
                    r = await client.get(
                        f"https://api.chownow.com/v1/restaurants/{restaurant_id}/orders",
                        headers=headers,
                    )
                elif op == "get_menu":
                    if not restaurant_id:
                        return ToolResult(ok=False, error="restaurant_id required")
                    r = await client.get(
                        f"https://api.chownow.com/v1/restaurants/{restaurant_id}/menu",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"ChowNow error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("chownow_api_request_failed")
                return ToolResult(ok=False, error=f"ChowNow communication failed: {exc}")


class OrdermarkApiTool(Tool):
    name = "ordermark_api"
    description = (
        "Interact with Ordermark API: get locations, list orders, "
        "and get order details."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "ordermark")
        if not creds:
            return ToolResult(
                ok=False,
                error="Ordermark not connected. "
                "Go to Integrations > Ordermark to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Ordermark API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_locations":
                    r = await client.get(
                        "https://api.ordermark.com/v1/locations",
                        headers=headers,
                    )
                elif op == "list_orders":
                    r = await client.get(
                        "https://api.ordermark.com/v1/orders",
                        headers=headers,
                    )
                elif op == "get_order":
                    order_id = _
                    if not order_id:
                        return ToolResult(ok=False, error="order_id required in kwargs")
                    r = await client.get(
                        f"https://api.ordermark.com/v1/orders/{order_id}",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Ordermark error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("ordermark_api_request_failed")
                return ToolResult(ok=False, error=f"Ordermark communication failed: {exc}")


class SliceApiTool(Tool):
    name = "slice_api"
    description = (
        "Interact with Slice API: get store info, list orders, "
        "and get menu data."
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
        creds = _resolve_creds(session, workspace_id, "slice")
        if not creds:
            return ToolResult(
                ok=False,
                error="Slice not connected. Go to Integrations > Slice to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Slice API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_store":
                    if not store_id:
                        return ToolResult(ok=False, error="store_id required")
                    r = await client.get(
                        f"https://api.slicelife.com/v1/stores/{store_id}",
                        headers=headers,
                    )
                elif op == "list_orders":
                    if not store_id:
                        return ToolResult(ok=False, error="store_id required")
                    r = await client.get(
                        f"https://api.slicelife.com/v1/stores/{store_id}/orders",
                        headers=headers,
                    )
                elif op == "get_menu":
                    if not store_id:
                        return ToolResult(ok=False, error="store_id required")
                    r = await client.get(
                        f"https://api.slicelife.com/v1/stores/{store_id}/menu",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Slice error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("slice_api_request_failed")
                return ToolResult(ok=False, error=f"Slice communication failed: {exc}")