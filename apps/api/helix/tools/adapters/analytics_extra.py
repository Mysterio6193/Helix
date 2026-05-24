"""Analytics and restaurant tool adapters: Mixpanel, Resy, OpenTable.

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

log = get_logger("helix.tools.analytics_extra")
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


class MixpanelApiTool(Tool):
    name = "mixpanel_api"
    description = (
        "Interact with Mixpanel API: get insights, list events, "
        "and get retention analytics."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        project_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "mixpanel")
        if not creds:
            return ToolResult(ok=False, error="Mixpanel not connected. Go to Integrations > Mixpanel to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Mixpanel service account secret required.")

        # Mixpanel uses project_id:secret as auth
        auth = (project_id, token) if project_id else (token, "")
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_insights":
                    r = await client.get(
                        "https://mixpanel.com/api/2.0/insights",
                        headers=headers,
                        auth=auth,
                    )
                elif op == "list_events":
                    r = await client.get(
                        "https://mixpanel.com/api/2.0/events/names",
                        headers=headers,
                        auth=auth,
                    )
                elif op == "get_retention":
                    r = await client.get(
                        "https://mixpanel.com/api/2.0/retention",
                        headers=headers,
                        auth=auth,
                        params={"from_date": "2024-01-01", "to_date": "2024-12-31"},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Mixpanel error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("mixpanel_api_request_failed")
                return ToolResult(ok=False, error=f"Mixpanel communication failed: {exc}")


class ResyApiTool(Tool):
    name = "resy_api"
    description = (
        "Interact with Resy API: get reservations and venue information."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        venue_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "resy")
        if not creds:
            return ToolResult(ok=False, error="Resy not connected. Go to Integrations > Resy to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Resy API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_venue":
                    if not venue_id:
                        return ToolResult(ok=False, error="venue_id required")
                    r = await client.get(
                        f"https://api.resy.com/3/venue/{venue_id}",
                        headers=headers,
                    )
                elif op == "get_reservations":
                    r = await client.get(
                        "https://api.resy.com/3/user/reservations",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Resy error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("resy_api_request_failed")
                return ToolResult(ok=False, error=f"Resy communication failed: {exc}")


class OpenTableApiTool(Tool):
    name = "opentable_api"
    description = (
        "Interact with OpenTable API: get reservations and list restaurants."
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
        creds = _resolve_creds(session, workspace_id, "opentable")
        if not creds:
            return ToolResult(ok=False, error="OpenTable not connected. Go to Integrations > OpenTable to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="OpenTable partner token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_reservations":
                    if not restaurant_id:
                        return ToolResult(ok=False, error="restaurant_id required")
                    r = await client.get(
                        f"https://platform.opentable.com/sync/v2/restaurants/{restaurant_id}/reservations",
                        headers=headers,
                        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
                    )
                elif op == "list_restaurants":
                    r = await client.get(
                        "https://platform.opentable.com/sync/v2/restaurants",
                        headers=headers,
                        params={"limit": 50},
                    )
                elif op == "get_availability":
                    if not restaurant_id:
                        return ToolResult(ok=False, error="restaurant_id required")
                    r = await client.get(
                        f"https://platform.opentable.com/sync/v2/restaurants/{restaurant_id}/availability",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"OpenTable error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("opentable_api_request_failed")
                return ToolResult(ok=False, error=f"OpenTable communication failed: {exc}")
