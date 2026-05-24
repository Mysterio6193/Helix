"""Productivity tool adapters: Airtable, Linear, Asana, Calendly.

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

log = get_logger("helix.tools.productivity_extra")
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


class AirtableApiTool(Tool):
    name = "airtable_api"
    description = (
        "Interact with Airtable API: list bases, get records, "
        "create records, and manage tables."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        base_id: str = "",
        table_id: str = "",
        record_data: dict | None = None,
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "airtable")
        if not creds:
            return ToolResult(ok=False, error="Airtable not connected. Go to Integrations > Airtable to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Airtable personal access token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "list_bases":
                    r = await client.get(
                        f"{settings.airtable_api_base.rstrip('/')}/v0/meta/bases",
                        headers=headers,
                    )
                elif op == "get_records":
                    if not base_id or not table_id:
                        return ToolResult(ok=False, error="base_id and table_id required")
                    r = await client.get(
                        f"{settings.airtable_api_base.rstrip('/')}/v0/{base_id}/{table_id}",
                        headers=headers,
                        params={"maxRecords": 100},
                    )
                elif op == "create_record":
                    if not base_id or not table_id or not record_data:
                        return ToolResult(ok=False, error="base_id, table_id, and record_data required")
                    r = await client.post(
                        f"{settings.airtable_api_base.rstrip('/')}/v0/{base_id}/{table_id}",
                        headers=headers,
                        json={"fields": record_data},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Airtable error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("airtable_api_request_failed")
                return ToolResult(ok=False, error=f"Airtable communication failed: {exc}")


class LinearApiTool(Tool):
    name = "linear_api"
    description = (
        "Interact with Linear API: get issues, create issues, "
        "get projects, and manage teams."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        title: str = "",
        team_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "linear")
        if not creds:
            return ToolResult(ok=False, error="Linear not connected. Go to Integrations > Linear to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Linear API key required.")

        headers = {"Authorization": token, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_issues":
                    r = await client.post(
                        f"{settings.linear_api_base.rstrip('/')}/graphql",
                        headers=headers,
                        json={"query": "{ issues { nodes { id title state { name } } } }"},
                    )
                elif op == "create_issue":
                    if not title or not team_id:
                        return ToolResult(ok=False, error="title and team_id required")
                    r = await client.post(
                        f"{settings.linear_api_base.rstrip('/')}/graphql",
                        headers=headers,
                        json={
                            "query": (
                                "mutation { issueCreate(input: { title: \"" + title + "\", teamId: \"" + team_id + "\" }) { issue { id title url } } }"
                            )
                        },
                    )
                elif op == "get_projects":
                    r = await client.post(
                        f"{settings.linear_api_base.rstrip('/')}/graphql",
                        headers=headers,
                        json={"query": "{ projects { nodes { id name state } } }"},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    data = r.json()
                    if data.get("errors"):
                        return ToolResult(ok=False, error=f"Linear GraphQL error: {data['errors']}")
                    return ToolResult(ok=True, data=data.get("data", {}))
                return ToolResult(ok=False, error=f"Linear error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("linear_api_request_failed")
                return ToolResult(ok=False, error=f"Linear communication failed: {exc}")


class AsanaApiTool(Tool):
    name = "asana_api"
    description = (
        "Interact with Asana API: get tasks, create tasks, "
        "get projects, and list workspaces."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        project_id: str = "",
        name: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "asana")
        if not creds:
            return ToolResult(ok=False, error="Asana not connected. Go to Integrations > Asana to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Asana personal access token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_tasks":
                    params = {"limit": 10}
                    if project_id:
                        params["project"] = project_id
                    r = await client.get(
                        "https://app.asana.com/api/1.0/tasks",
                        headers=headers,
                        params=params,
                    )
                elif op == "create_task":
                    if not name:
                        return ToolResult(ok=False, error="name required")
                    payload = {"data": {"name": name}}
                    if project_id:
                        payload["data"]["projects"] = [project_id]
                    r = await client.post(
                        "https://app.asana.com/api/1.0/tasks",
                        headers=headers,
                        json=payload,
                    )
                elif op == "get_projects":
                    r = await client.get(
                        "https://app.asana.com/api/1.0/projects",
                        headers=headers,
                        params={"limit": 10},
                    )
                elif op == "get_workspaces":
                    r = await client.get(
                        "https://app.asana.com/api/1.0/workspaces",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Asana error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("asana_api_request_failed")
                return ToolResult(ok=False, error=f"Asana communication failed: {exc}")


class CalendlyApiTool(Tool):
    name = "calendly_api"
    description = (
        "Interact with Calendly API: get scheduled events, "
        "list event types, and get scheduling links."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        user_uri: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "calendly")
        if not creds:
            return ToolResult(ok=False, error="Calendly not connected. Go to Integrations > Calendly to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Calendly personal access token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_events":
                    r = await client.get(
                        "https://api.calendly.com/scheduled_events",
                        headers=headers,
                        params={"count": 10},
                    )
                elif op == "list_event_types":
                    if not user_uri:
                        return ToolResult(ok=False, error="user_uri required")
                    r = await client.get(
                        "https://api.calendly.com/event_types",
                        headers=headers,
                        params={"user": user_uri},
                    )
                elif op == "get_user":
                    r = await client.get(
                        "https://api.calendly.com/users/me",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Calendly error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("calendly_api_request_failed")
                return ToolResult(ok=False, error=f"Calendly communication failed: {exc}")
