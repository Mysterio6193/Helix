"""Social and analytics tool adapters: Twitter/X, PostHog, Threads, TikTok, Pinterest.

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

log = get_logger("helix.tools.social")
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


class TwitterApiTool(Tool):
    name = "twitter_api"
    description = (
        "Interact with X/Twitter API: post tweets, get timeline, "
        "and get user information."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        text: str = "",
        username: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "twitter")
        if not creds:
            return ToolResult(ok=False, error="Twitter not connected. Go to Integrations > Twitter to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Twitter bearer token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "post_tweet":
                    if not text:
                        return ToolResult(ok=False, error="text required")
                    r = await client.post(
                        "https://api.twitter.com/2/tweets",
                        headers=headers,
                        json={"text": text},
                    )
                elif op == "get_user":
                    if not username:
                        return ToolResult(ok=False, error="username required")
                    r = await client.get(
                        f"https://api.twitter.com/2/users/by/username/{username}",
                        headers=headers,
                    )
                elif op == "get_timeline":
                    r = await client.get(
                        "https://api.twitter.com/2/users/me/tweets",
                        headers=headers,
                        params={"max_results": 10},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Twitter error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("twitter_api_request_failed")
                return ToolResult(ok=False, error=f"Twitter communication failed: {exc}")


class PostHogApiTool(Tool):
    name = "posthog_api"
    description = (
        "Interact with PostHog API: get insights, list events, "
        "and get funnel analytics."
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
        creds = _resolve_creds(session, workspace_id, "posthog")
        if not creds:
            return ToolResult(ok=False, error="PostHog not connected. Go to Integrations > PostHog to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="PostHog personal API key required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_insights":
                    if not project_id:
                        return ToolResult(ok=False, error="project_id required")
                    r = await client.get(
                        f"https://app.posthog.com/api/projects/{project_id}/insights",
                        headers=headers,
                    )
                elif op == "list_events":
                    if not project_id:
                        return ToolResult(ok=False, error="project_id required")
                    r = await client.get(
                        f"https://app.posthog.com/api/projects/{project_id}/events",
                        headers=headers,
                        params={"limit": 100},
                    )
                elif op == "get_funnel":
                    if not project_id:
                        return ToolResult(ok=False, error="project_id required")
                    r = await client.get(
                        f"https://app.posthog.com/api/projects/{project_id}/insights/funnels",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"PostHog error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("posthog_api_request_failed")
                return ToolResult(ok=False, error=f"PostHog communication failed: {exc}")


class ThreadsApiTool(Tool):
    name = "threads_api"
    description = (
        "Interact with Threads API: publish threads and get insights."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        text: str = "",
        media_url: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "threads")
        if not creds:
            return ToolResult(ok=False, error="Threads not connected. Go to Integrations > Threads to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Threads access token required.")

        api_version = settings.meta_graph_api_version or "v19.0"
        base = f"https://graph.facebook.com/{api_version}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "publish_thread":
                    if not text:
                        return ToolResult(ok=False, error="text required")
                    r = await client.post(
                        f"{base}/me/threads",
                        params={"access_token": token},
                        json={"text": text, "media_type": "TEXT"},
                    )
                elif op == "get_insights":
                    r = await client.get(
                        f"{base}/me/threads_insights",
                        params={"access_token": token, "metric": "views,replies,reposts"},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Threads error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("threads_api_request_failed")
                return ToolResult(ok=False, error=f"Threads communication failed: {exc}")


class TikTokApiTool(Tool):
    name = "tiktok_api"
    description = (
        "Interact with TikTok Business API: upload videos, get insights, "
        "and list posts."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        advertiser_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "tiktok_business")
        if not creds:
            return ToolResult(ok=False, error="TikTok Business not connected. Go to Integrations > TikTok Business to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="TikTok access token required.")

        headers = {"Access-Token": token, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "get_insights":
                    if not advertiser_id:
                        return ToolResult(ok=False, error="advertiser_id required")
                    r = await client.get(
                        "https://business-api.tiktok.com/open_api/v1.3/ advertiser/insights",
                        headers=headers,
                        params={"advertiser_id": advertiser_id, "report_type": "BASIC", "data_level": "AUCTION_AD"},
                    )
                elif op == "list_posts":
                    if not advertiser_id:
                        return ToolResult(ok=False, error="advertiser_id required")
                    r = await client.get(
                        "https://business-api.tiktok.com/open_api/v1.3/ advertiser/posts",
                        headers=headers,
                        params={"advertiser_id": advertiser_id, "limit": 10},
                    )
                elif op == "get_advertiser_info":
                    r = await client.get(
                        "https://business-api.tiktok.com/open_api/v1.3/ advertiser/info",
                        headers=headers,
                        params={"advertiser_ids": f"[{advertiser_id}]"} if advertiser_id else {},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code == 200:
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"TikTok error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("tiktok_api_request_failed")
                return ToolResult(ok=False, error=f"TikTok communication failed: {exc}")


class PinterestApiTool(Tool):
    name = "pinterest_api"
    description = (
        "Interact with Pinterest API: create pins, get boards, "
        "and get analytics."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        board_id: str = "",
        title: str = "",
        image_url: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "pinterest")
        if not creds:
            return ToolResult(ok=False, error="Pinterest not connected. Go to Integrations > Pinterest to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Pinterest access token required.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "create_pin":
                    if not board_id or not title:
                        return ToolResult(ok=False, error="board_id and title required")
                    payload = {
                        "title": title,
                        "board_id": board_id,
                        "description": title,
                    }
                    if image_url:
                        payload["media_source"] = {"source_type": "image_url", "url": image_url}
                    r = await client.post(
                        "https://api.pinterest.com/v5/pins",
                        headers=headers,
                        json=payload,
                    )
                elif op == "get_boards":
                    r = await client.get(
                        "https://api.pinterest.com/v5/boards",
                        headers=headers,
                        params={"page_size": 25},
                    )
                elif op == "get_analytics":
                    r = await client.get(
                        "https://api.pinterest.com/v5/user_account/analytics",
                        headers=headers,
                        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Pinterest error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("pinterest_api_request_failed")
                return ToolResult(ok=False, error=f"Pinterest communication failed: {exc}")
