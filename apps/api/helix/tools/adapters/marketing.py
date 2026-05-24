"""Marketing tool adapters: Mailchimp, HubSpot, SendGrid, Google Business.

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

log = get_logger("helix.tools.marketing")
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


class MailchimpApiTool(Tool):
    name = "mailchimp_api"
    description = (
        "Interact with Mailchimp API: list campaigns, send campaigns, "
        "get audience lists, and manage subscribers."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        list_id: str = "",
        campaign_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "mailchimp")
        if not creds:
            return ToolResult(ok=False, error="Mailchimp not connected. Go to Integrations > Mailchimp to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Mailchimp API key required.")

        # Extract datacenter from API key (last part after dash)
        datacenter = "us1"
        if "-" in token:
            datacenter = token.split("-")[-1]

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        base = f"https://{datacenter}.api.mailchimp.com/3.0"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "list_campaigns":
                    r = await client.get(f"{base}/campaigns", headers=headers, params={"count": 10})
                elif op == "send_campaign":
                    if not campaign_id:
                        return ToolResult(ok=False, error="campaign_id required")
                    r = await client.post(f"{base}/campaigns/{campaign_id}/actions/send", headers=headers)
                elif op == "list_lists":
                    r = await client.get(f"{base}/lists", headers=headers, params={"count": 10})
                elif op == "get_list_members":
                    if not list_id:
                        return ToolResult(ok=False, error="list_id required")
                    r = await client.get(f"{base}/lists/{list_id}/members", headers=headers, params={"count": 50})
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201, 204):
                    return ToolResult(ok=True, data=r.json() if r.status_code != 204 else {"sent": True})
                return ToolResult(ok=False, error=f"Mailchimp error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("mailchimp_api_request_failed")
                return ToolResult(ok=False, error=f"Mailchimp communication failed: {exc}")


class HubSpotApiTool(Tool):
    name = "hubspot_api"
    description = (
        "Interact with HubSpot API: get contacts, create deals, "
        "get pipeline stages, and manage CRM objects."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "hubspot")
        if not creds:
            return ToolResult(ok=False, error="HubSpot not connected. Go to Integrations > HubSpot to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="HubSpot private app token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_contacts":
                    r = await client.get(
                        "https://api.hubapi.com/crm/v3/objects/contacts",
                        headers=headers,
                        params={"limit": 10},
                    )
                elif op == "create_deal":
                    r = await client.post(
                        "https://api.hubapi.com/crm/v3/objects/deals",
                        headers=headers,
                        json={"properties": {"dealname": "Helix Deal", "pipeline": "default"}},
                    )
                elif op == "get_pipeline":
                    r = await client.get(
                        "https://api.hubapi.com/crm/v3/pipelines/deals",
                        headers=headers,
                    )
                elif op == "get_companies":
                    r = await client.get(
                        "https://api.hubapi.com/crm/v3/objects/companies",
                        headers=headers,
                        params={"limit": 10},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"HubSpot error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("hubspot_api_request_failed")
                return ToolResult(ok=False, error=f"HubSpot communication failed: {exc}")


class SendGridApiTool(Tool):
    name = "sendgrid_api"
    description = (
        "Interact with SendGrid API: send emails, get stats, "
        "and list email templates."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        to_email: str = "",
        subject: str = "",
        content: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "sendgrid")
        if not creds:
            return ToolResult(ok=False, error="SendGrid not connected. Go to Integrations > SendGrid to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="SendGrid API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "send_email":
                    if not to_email or not subject:
                        return ToolResult(ok=False, error="to_email and subject required")
                    r = await client.post(
                        f"{settings.sendgrid_api_base.rstrip('/')}/v3/mail/send",
                        headers=headers,
                        json={
                            "personalizations": [{"to": [{"email": to_email}]}],
                            "from": {"email": "noreply@helix.ai"},
                            "subject": subject,
                            "content": [{"type": "text/plain", "value": content}],
                        },
                    )
                elif op == "get_stats":
                    r = await client.get(
                        f"{settings.sendgrid_api_base.rstrip('/')}/v3/stats",
                        headers=headers,
                        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
                    )
                elif op == "list_templates":
                    r = await client.get(
                        f"{settings.sendgrid_api_base.rstrip('/')}/v3/templates",
                        headers=headers,
                        params={"generations": "dynamic"},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201, 202):
                    return ToolResult(ok=True, data=r.json() if r.status_code != 202 else {"sent": True})
                return ToolResult(ok=False, error=f"SendGrid error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("sendgrid_api_request_failed")
                return ToolResult(ok=False, error=f"SendGrid communication failed: {exc}")


class GoogleBusinessApiTool(Tool):
    name = "google_business_api"
    description = (
        "Interact with Google Business Profile API: get profile info, "
        "post updates, and get reviews."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        account_name: str = "",
        location_name: str = "",
        post_summary: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "google_business")
        if not creds:
            return ToolResult(ok=False, error="Google Business not connected. Go to Integrations > Google Business to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Google Business access token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_profile":
                    if not account_name or not location_name:
                        return ToolResult(ok=False, error="account_name and location_name required")
                    r = await client.get(
                        f"https://mybusiness.googleapis.com/v4/{account_name}/{location_name}",
                        headers=headers,
                    )
                elif op == "post_update":
                    if not location_name or not post_summary:
                        return ToolResult(ok=False, error="location_name and post_summary required")
                    r = await client.post(
                        f"https://mybusiness.googleapis.com/v4/{location_name}/localPosts",
                        headers=headers,
                        json={"summary": post_summary, "languageCode": "en", "topicType": "STANDARD"},
                    )
                elif op == "get_reviews":
                    if not location_name:
                        return ToolResult(ok=False, error="location_name required")
                    r = await client.get(
                        f"https://mybusiness.googleapis.com/v4/{location_name}/reviews",
                        headers=headers,
                        params={"pageSize": 10},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Google Business error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("google_business_api_request_failed")
                return ToolResult(ok=False, error=f"Google Business communication failed: {exc}")
