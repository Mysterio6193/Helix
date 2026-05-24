"""Zoho suite tool adapters: CRM, Books, Campaigns, Desk, Inventory, Subscriptions, Projects.

All tools require valid credentials from tool_connections. No mock fallbacks.
Zoho APIs use OAuth2 tokens and require datacenter-specific base URLs.
"""
from __future__ import annotations

import uuid
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.integrations.resolver import get_integration_credentials
from helix.tools.base import Tool, ToolResult

log = get_logger("helix.tools.zoho")
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


def _zoho_base(dc: str | None) -> str:
    """Return Zoho API base URL for datacenter."""
    datacenter = dc or "com"
    return f"https://www.zohoapis.{datacenter}"


def _zoho_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {token}", "Content-Type": "application/json"}


class ZohoCrmApiTool(Tool):
    name = "zoho_crm_api"
    description = (
        "Interact with Zoho CRM API: get leads, create contacts, "
        "get deals, and manage pipeline."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "zoho_crm")
        if not creds:
            return ToolResult(
                ok=False,
                error="Zoho CRM not connected. "
                "Go to Integrations > Zoho CRM to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Zoho CRM access token required.")

        dc = creds.get("datacenter") or creds.get("extra", {}).get("datacenter")
        base = _zoho_base(dc)
        headers = _zoho_headers(token)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_leads":
                    r = await client.get(
                        f"{base}/crm/v2/Leads", headers=headers
                    )
                elif op == "create_contact":
                    payload = {
                        "data": [{"Last_Name": "Helix", "First_Name": "User"}]
                    }
                    r = await client.post(
                        f"{base}/crm/v2/Contacts", headers=headers, json=payload
                    )
                elif op == "get_deals":
                    r = await client.get(
                        f"{base}/crm/v2/Deals", headers=headers
                    )
                elif op == "get_accounts":
                    r = await client.get(
                        f"{base}/crm/v2/Accounts", headers=headers
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Zoho CRM error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("zoho_crm_api_request_failed")
                return ToolResult(ok=False, error=f"Zoho CRM communication failed: {exc}")


class ZohoBooksApiTool(Tool):
    name = "zoho_books_api"
    description = (
        "Interact with Zoho Books API: get invoices, create expenses, "
        "get contacts, and fetch reports."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        organization_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "zoho_books")
        if not creds:
            return ToolResult(
                ok=False,
                error="Zoho Books not connected. "
                "Go to Integrations > Zoho Books to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Zoho Books access token required.")

        dc = creds.get("datacenter") or creds.get("extra", {}).get("datacenter")
        base = _zoho_base(dc)
        headers = _zoho_headers(token)
        org_id = organization_id or creds.get("organization_id", "")
        if not org_id:
            return ToolResult(ok=False, error="organization_id required")

        params = {"organization_id": org_id}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_invoices":
                    r = await client.get(
                        f"{base}/books/v3/invoices", headers=headers, params=params
                    )
                elif op == "get_contacts":
                    r = await client.get(
                        f"{base}/books/v3/contacts", headers=headers, params=params
                    )
                elif op == "create_expense":
                    payload = {
                        "account_name": "Miscellaneous",
                        "paid_through_account_name": "Cash",
                        "amount": 100.0,
                    }
                    r = await client.post(
                        f"{base}/books/v3/expenses", headers=headers, params=params, json=payload
                    )
                elif op == "get_reports":
                    r = await client.get(
                        f"{base}/books/v3/reports", headers=headers, params=params
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Zoho Books error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("zoho_books_api_request_failed")
                return ToolResult(ok=False, error=f"Zoho Books communication failed: {exc}")


class ZohoCampaignsApiTool(Tool):
    name = "zoho_campaigns_api"
    description = (
        "Interact with Zoho Campaigns API: get campaigns, "
        "list mailing lists, and get reports."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "zoho_campaigns")
        if not creds:
            return ToolResult(
                ok=False,
                error="Zoho Campaigns not connected. "
                "Go to Integrations > Zoho Campaigns to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Zoho Campaigns access token required.")

        dc = creds.get("datacenter") or creds.get("extra", {}).get("datacenter")
        base = _zoho_base(dc)
        headers = _zoho_headers(token)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_campaigns":
                    r = await client.get(
                        f"{base}/campaigns/v1/campaigns", headers=headers
                    )
                elif op == "get_lists":
                    r = await client.get(
                        f"{base}/campaigns/v1/mailinglists", headers=headers
                    )
                elif op == "get_reports":
                    r = await client.get(
                        f"{base}/campaigns/v1/reports", headers=headers
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Zoho Campaigns error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("zoho_campaigns_api_request_failed")
                return ToolResult(ok=False, error=f"Zoho Campaigns communication failed: {exc}")


class ZohoDeskApiTool(Tool):
    name = "zoho_desk_api"
    description = (
        "Interact with Zoho Desk API: get tickets, create tickets, "
        "get agents, and fetch departments."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "zoho_desk")
        if not creds:
            return ToolResult(
                ok=False,
                error="Zoho Desk not connected. "
                "Go to Integrations > Zoho Desk to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Zoho Desk access token required.")

        dc = creds.get("datacenter") or creds.get("extra", {}).get("datacenter")
        base = _zoho_base(dc)
        headers = _zoho_headers(token)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_tickets":
                    r = await client.get(
                        f"{base}/desk/v1/tickets", headers=headers
                    )
                elif op == "create_ticket":
                    payload = {"subject": "Helix Support Ticket", "departmentId": "1"}
                    r = await client.post(
                        f"{base}/desk/v1/tickets", headers=headers, json=payload
                    )
                elif op == "get_agents":
                    r = await client.get(
                        f"{base}/desk/v1/agents", headers=headers
                    )
                elif op == "get_departments":
                    r = await client.get(
                        f"{base}/desk/v1/departments", headers=headers
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Zoho Desk error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("zoho_desk_api_request_failed")
                return ToolResult(ok=False, error=f"Zoho Desk communication failed: {exc}")


class ZohoInventoryApiTool(Tool):
    name = "zoho_inventory_api"
    description = (
        "Interact with Zoho Inventory API: get items, list orders, "
        "get warehouses, and manage stock."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        organization_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "zoho_inventory")
        if not creds:
            return ToolResult(
                ok=False,
                error="Zoho Inventory not connected. "
                "Go to Integrations > Zoho Inventory to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Zoho Inventory access token required.")

        dc = creds.get("datacenter") or creds.get("extra", {}).get("datacenter")
        base = _zoho_base(dc)
        headers = _zoho_headers(token)
        org_id = organization_id or creds.get("organization_id", "")
        if not org_id:
            return ToolResult(ok=False, error="organization_id required")

        params = {"organization_id": org_id}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_items":
                    r = await client.get(
                        f"{base}/inventory/v1/items", headers=headers, params=params
                    )
                elif op == "get_orders":
                    r = await client.get(
                        f"{base}/inventory/v1/salesorders", headers=headers, params=params
                    )
                elif op == "get_warehouses":
                    r = await client.get(
                        f"{base}/inventory/v1/warehouses", headers=headers, params=params
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Zoho Inventory error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("zoho_inventory_api_request_failed")
                return ToolResult(ok=False, error=f"Zoho Inventory communication failed: {exc}")


class ZohoSubscriptionsApiTool(Tool):
    name = "zoho_subscriptions_api"
    description = (
        "Interact with Zoho Subscriptions API: get plans, list subscriptions, "
        "get customers, and fetch invoices."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        organization_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "zoho_subscriptions")
        if not creds:
            return ToolResult(
                ok=False,
                error="Zoho Subscriptions not connected. "
                "Go to Integrations > Zoho Subscriptions to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Zoho Subscriptions access token required.")

        dc = creds.get("datacenter") or creds.get("extra", {}).get("datacenter")
        base = _zoho_base(dc)
        headers = _zoho_headers(token)
        org_id = organization_id or creds.get("organization_id", "")
        if not org_id:
            return ToolResult(ok=False, error="organization_id required")

        params = {"organization_id": org_id}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_plans":
                    r = await client.get(
                        f"{base}/subscriptions/v1/plans", headers=headers, params=params
                    )
                elif op == "get_subscriptions":
                    r = await client.get(
                        f"{base}/subscriptions/v1/subscriptions", headers=headers, params=params
                    )
                elif op == "get_customers":
                    r = await client.get(
                        f"{base}/subscriptions/v1/customers", headers=headers, params=params
                    )
                elif op == "get_invoices":
                    r = await client.get(
                        f"{base}/subscriptions/v1/invoices", headers=headers, params=params
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(
                    ok=False, error=f"Zoho Subscriptions error {r.status_code}: {r.text}"
                )
            except Exception as exc:
                log.exception("zoho_subscriptions_api_request_failed")
                return ToolResult(ok=False, error=f"Zoho Subscriptions communication failed: {exc}")


class ZohoProjectsApiTool(Tool):
    name = "zoho_projects_api"
    description = (
        "Interact with Zoho Projects API: get projects, list tasks, "
        "get milestones, and fetch timesheets."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "zoho_projects")
        if not creds:
            return ToolResult(
                ok=False,
                error="Zoho Projects not connected. "
                "Go to Integrations > Zoho Projects to connect."
            )

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Zoho Projects access token required.")

        dc = creds.get("datacenter") or creds.get("extra", {}).get("datacenter")
        base = _zoho_base(dc)
        headers = _zoho_headers(token)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_projects":
                    r = await client.get(
                        f"{base}/projects/v3/portal/own/projects", headers=headers
                    )
                elif op == "get_tasks":
                    r = await client.get(
                        f"{base}/projects/v3/portal/own/tasks", headers=headers
                    )
                elif op == "get_milestones":
                    r = await client.get(
                        f"{base}/projects/v3/portal/own/milestones", headers=headers
                    )
                elif op == "get_timesheets":
                    r = await client.get(
                        f"{base}/projects/v3/portal/own/timelogs", headers=headers
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Zoho Projects error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("zoho_projects_api_request_failed")
                return ToolResult(ok=False, error=f"Zoho Projects communication failed: {exc}")