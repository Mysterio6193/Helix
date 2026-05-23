"""Skill-facing helper: invoke a productivity tool with credentials resolved
from `tool_connections` for the calling workspace.

Example:
    from helix.integrations.invoke import invoke_provider_tool

    result = await invoke_provider_tool(
        ctx,
        tool_name="notion_api",
        provider="notion",
        op="create_page",
        parent_database_id=db_id,
        title="Launch board",
    )

Skills should prefer this over `get_tool(...).call(access_token=...)` so that
token loading, refresh, and provider-aware error messages stay in one place.
"""
from __future__ import annotations

from typing import Any

from helix.integrations.resolver import get_access_token
from helix.skills.base import SkillContext
from helix.tools.base import ToolResult
from helix.tools.registry import get_tool


async def invoke_provider_tool(
    ctx: SkillContext,
    *,
    tool_name: str,
    provider: str,
    account_label: str | None = None,
    **kwargs: Any,
) -> ToolResult:
    tool = get_tool(tool_name)
    if tool is None:
        return ToolResult(ok=False, error=f"tool not registered: {tool_name}")
    if ctx.workspace_id is None:
        return ToolResult(ok=False, error="workspace_id missing on skill context")

    access_token = await get_access_token(
        ctx.db,
        workspace_id=ctx.workspace_id,
        provider=provider,
        account_label=account_label,
    )
    if not access_token:
        return ToolResult(
            ok=False,
            error=f"{provider} not connected for this workspace",
        )
    return await tool.call(access_token=access_token, **kwargs)
