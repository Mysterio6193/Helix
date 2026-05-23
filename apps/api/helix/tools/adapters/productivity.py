"""Productivity adapters: Canva, Figma, Notion, Gmail (draft), Web Search."""
from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.tools.base import Tool, ToolResult


class CanvaConnectTool(Tool):
    name = "canva_connect"
    description = "Canva Connect API: create design and upload asset."

    BASE = "https://api.canva.com/rest/v1"

    async def _call(
        self,
        *,
        access_token: str,
        op: str,
        design_type: str = "InstagramPost",
        title: str | None = None,
        asset_bytes: bytes | None = None,
        asset_mime: str = "image/png",
        asset_name: str = "asset.png",
        design_id: str | None = None,
        **_: Any,
    ) -> ToolResult:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=120, headers=headers) as http:
            if op == "create_design":
                resp = await http.post(
                    f"{self.BASE}/designs",
                    json={"design_type": design_type, "title": title or "Helix design"},
                )
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"canva create_design {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            if op == "upload_asset":
                if asset_bytes is None:
                    return ToolResult(ok=False, error="asset_bytes required")
                resp = await http.post(
                    f"{self.BASE}/asset-uploads",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": asset_mime,
                        "Asset-Upload-Metadata": f'{{"name_base64":"{base64.b64encode(asset_name.encode()).decode()}"}}',
                    },
                    content=asset_bytes,
                )
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"canva upload_asset {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            if op == "export":
                if not design_id:
                    return ToolResult(ok=False, error="design_id required")
                resp = await http.post(
                    f"{self.BASE}/exports",
                    json={"design_id": design_id, "format": {"type": "png"}},
                )
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"canva export {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            return ToolResult(ok=False, error=f"unknown op: {op}")


class FigmaApiTool(Tool):
    name = "figma_api"
    description = "Figma REST: read file components and styles."

    BASE = "https://api.figma.com/v1"

    async def _call(
        self,
        *,
        access_token: str,
        op: str,
        file_key: str | None = None,
        node_ids: list[str] | None = None,
        **_: Any,
    ) -> ToolResult:
        headers = {"X-Figma-Token": access_token}
        async with httpx.AsyncClient(timeout=60, headers=headers) as http:
            if op == "get_file":
                if not file_key:
                    return ToolResult(ok=False, error="file_key required")
                resp = await http.get(f"{self.BASE}/files/{file_key}")
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"figma get_file {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            if op == "get_components":
                if not file_key:
                    return ToolResult(ok=False, error="file_key required")
                resp = await http.get(f"{self.BASE}/files/{file_key}/components")
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"figma get_components {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            if op == "get_nodes":
                if not file_key or not node_ids:
                    return ToolResult(ok=False, error="file_key + node_ids required")
                resp = await http.get(
                    f"{self.BASE}/files/{file_key}/nodes",
                    params={"ids": ",".join(node_ids)},
                )
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"figma get_nodes {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            return ToolResult(ok=False, error=f"unknown op: {op}")


class NotionApiTool(Tool):
    name = "notion_api"
    description = "Notion API: create pages / blocks for campaign boards."

    BASE = "https://api.notion.com/v1"

    async def _call(
        self,
        *,
        access_token: str,
        op: str,
        parent_database_id: str | None = None,
        parent_page_id: str | None = None,
        title: str = "Helix campaign",
        properties: dict | None = None,
        children: list | None = None,
        page_id: str | None = None,
        block_id: str | None = None,
        blocks: list | None = None,
        **_: Any,
    ) -> ToolResult:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60, headers=headers) as http:
            if op == "create_page":
                if parent_database_id:
                    parent = {"database_id": parent_database_id}
                elif parent_page_id:
                    parent = {"page_id": parent_page_id}
                else:
                    return ToolResult(ok=False, error="parent_database_id or parent_page_id required")
                payload: dict[str, Any] = {
                    "parent": parent,
                    "properties": properties
                    or {
                        "title": {
                            "title": [{"type": "text", "text": {"content": title}}]
                        }
                    },
                }
                if children:
                    payload["children"] = children
                resp = await http.post(f"{self.BASE}/pages", json=payload)
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"notion create_page {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            if op == "append_blocks":
                target = block_id or page_id
                if not target:
                    return ToolResult(ok=False, error="block_id or page_id required")
                resp = await http.patch(
                    f"{self.BASE}/blocks/{target}/children",
                    json={"children": blocks or []},
                )
                if resp.status_code >= 400:
                    return ToolResult(ok=False, error=f"notion append_blocks {resp.status_code}: {resp.text}")
                return ToolResult(ok=True, data=resp.json())
            return ToolResult(ok=False, error=f"unknown op: {op}")


class GmailDraftTool(Tool):
    """Gmail draft creation only — never sends. User must review and send.

    Note: this builds a draft via the Gmail REST API. Auto-sending email on behalf
    of users is explicitly out of scope for safety reasons.
    """

    name = "gmail_draft"
    description = "Create a Gmail draft (does not send)."

    BASE = "https://gmail.googleapis.com/gmail/v1"

    async def _call(
        self,
        *,
        access_token: str,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        html: bool = False,
        **_: Any,
    ) -> ToolResult:
        msg = EmailMessage()
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc
        msg["Subject"] = subject
        if html:
            msg.set_content("(See HTML body)")
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60, headers=headers) as http:
            resp = await http.post(
                f"{self.BASE}/users/me/drafts",
                json={"message": {"raw": raw}},
            )
            if resp.status_code >= 400:
                return ToolResult(ok=False, error=f"gmail draft {resp.status_code}: {resp.text}")
            return ToolResult(ok=True, data=resp.json())


class WebSearchTool(Tool):
    name = "web_search"
    description = "Brave Search API for trend / competitor / review research."

    async def _call(
        self,
        *,
        query: str,
        count: int = 10,
        country: str = "US",
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.brave_api_key:
            return ToolResult(ok=False, error="BRAVE_API_KEY not configured")
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": settings.brave_api_key,
        }
        async with httpx.AsyncClient(timeout=30, headers=headers) as http:
            resp = await http.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": count, "country": country},
            )
            if resp.status_code >= 400:
                return ToolResult(ok=False, error=f"brave search {resp.status_code}: {resp.text}")
            body = resp.json()
            results = []
            for item in (body.get("web", {}) or {}).get("results", []):
                results.append(
                    {
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "description": item.get("description"),
                        "age": item.get("age"),
                    }
                )
            return ToolResult(ok=True, data=results, metadata={"query": query})
