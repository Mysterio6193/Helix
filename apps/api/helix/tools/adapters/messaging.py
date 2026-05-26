"""Messaging tool adapters: Slack, Discord, WhatsApp Business, Meta Pages, Instagram, Telegram.

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

log = get_logger("helix.tools.messaging")
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


class SlackApiTool(Tool):
    name = "slack_api"
    description = (
        "Interact with Slack API: post messages to channels, list channels, "
        "get user info, and manage conversations."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        channel: str = "#general",
        text: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "slack")
        if not creds:
            return ToolResult(ok=False, error="Slack not connected. Go to Integrations > Slack to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Slack credentials incomplete. Reconnect your workspace.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "post_message":
                    if not text:
                        return ToolResult(ok=False, error="text required")
                    r = await client.post(
                        f"{settings.slack_api_base.rstrip('/')}/chat.postMessage",
                        headers=headers,
                        json={"channel": channel, "text": text},
                    )
                elif op == "list_channels":
                    r = await client.get(
                        f"{settings.slack_api_base.rstrip('/')}/conversations.list",
                        headers=headers,
                        params={"limit": 100, "types": "public_channel,private_channel"},
                    )
                elif op == "get_user_info":
                    r = await client.get(
                        f"{settings.slack_api_base.rstrip('/')}/auth.test",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                data = r.json()
                if data.get("ok") or r.status_code in (200, 201):
                    return ToolResult(ok=True, data=data)
                return ToolResult(ok=False, error=f"Slack error: {data.get('error', r.text)}")
            except Exception as exc:
                log.exception("slack_api_request_failed")
                return ToolResult(ok=False, error=f"Slack communication failed: {exc}")


class DiscordApiTool(Tool):
    name = "discord_api"
    description = (
        "Interact with Discord API: post messages to channels, list guilds, "
        "and get member information."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        channel_id: str = "",
        content: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "discord")
        if not creds:
            return ToolResult(ok=False, error="Discord not connected. Go to Integrations > Discord to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Discord credentials incomplete. Reconnect your bot.")

        headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "post_message":
                    if not channel_id or not content:
                        return ToolResult(ok=False, error="channel_id and content required")
                    r = await client.post(
                        f"https://discord.com/api/v10/channels/{channel_id}/messages",
                        headers=headers,
                        json={"content": content},
                    )
                elif op == "list_guilds":
                    r = await client.get(
                        "https://discord.com/api/v10/users/@me/guilds",
                        headers=headers,
                    )
                elif op == "get_bot_info":
                    r = await client.get(
                        "https://discord.com/api/v10/users/@me",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Discord error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("discord_api_request_failed")
                return ToolResult(ok=False, error=f"Discord communication failed: {exc}")


class WhatsAppApiTool(Tool):
    name = "whatsapp_api"
    description = (
        "Interact with WhatsApp Business API: send messages, get message templates, "
        "and list conversations."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        to: str = "",
        template_name: str = "",
        language_code: str = "en",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "whatsapp_business")
        if not creds:
            return ToolResult(ok=False, error="WhatsApp Business not connected. Go to Integrations > WhatsApp Business to connect.")

        token = creds.get("token")
        phone_number_id = creds.get("phone_number_id") or creds.get("extra", {}).get("phone_number_id")
        if not token or not phone_number_id:
            return ToolResult(ok=False, error="WhatsApp credentials incomplete. Need token and phone_number_id.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        base = f"https://graph.facebook.com/v19.0/{phone_number_id}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "send_template":
                    if not to or not template_name:
                        return ToolResult(ok=False, error="to and template_name required")
                    r = await client.post(
                        f"{base}/messages",
                        headers=headers,
                        json={
                            "messaging_product": "whatsapp",
                            "to": to,
                            "type": "template",
                            "template": {"name": template_name, "language": {"code": language_code}},
                        },
                    )
                elif op == "list_templates":
                    business_id = creds.get("business_id") or creds.get("extra", {}).get("business_id")
                    if not business_id:
                        return ToolResult(ok=False, error="business_id required for listing templates")
                    r = await client.get(
                        f"https://graph.facebook.com/v19.0/{business_id}/message_templates",
                        headers=headers,
                    )
                elif op == "get_phone_numbers":
                    r = await client.get(
                        f"{base}",
                        headers=headers,
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"WhatsApp error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("whatsapp_api_request_failed")
                return ToolResult(ok=False, error=f"WhatsApp communication failed: {exc}")


class MetaPagesApiTool(Tool):
    name = "meta_pages_api"
    description = (
        "Interact with Facebook Pages API: post to page, get insights, "
        "and list posts."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        message: str = "",
        page_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "meta_pages")
        if not creds:
            return ToolResult(ok=False, error="Facebook Pages not connected. Go to Integrations > Facebook Pages to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Facebook Pages credentials incomplete.")

        api_version = settings.meta_graph_api_version or "v19.0"
        base = f"https://graph.facebook.com/{api_version}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "post_to_page":
                    if not page_id or not message:
                        return ToolResult(ok=False, error="page_id and message required")
                    r = await client.post(
                        f"{base}/{page_id}/feed",
                        params={"access_token": token},
                        json={"message": message},
                    )
                elif op == "get_insights":
                    if not page_id:
                        return ToolResult(ok=False, error="page_id required")
                    r = await client.get(
                        f"{base}/{page_id}/insights",
                        params={"access_token": token, "metric": "page_impressions,page_engaged_users"},
                    )
                elif op == "list_posts":
                    if not page_id:
                        return ToolResult(ok=False, error="page_id required")
                    r = await client.get(
                        f"{base}/{page_id}/posts",
                        params={"access_token": token, "limit": 10},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Meta Pages error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("meta_pages_api_request_failed")
                return ToolResult(ok=False, error=f"Meta Pages communication failed: {exc}")


class TelegramApiTool(Tool):
    name = "telegram_api"
    description = (
        "Interact with Telegram Bot API: send messages to chats, get updates, "
        "get bot info, and manage the webhook."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        chat_id: str = "",
        text: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "telegram")
        if not creds:
            return ToolResult(ok=False, error="Telegram not connected. Go to Integrations > Telegram to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Telegram credentials incomplete. Reconnect your bot.")

        base = f"https://api.telegram.org/bot{token}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "send_message":
                    if not chat_id or not text:
                        return ToolResult(ok=False, error="chat_id and text required")
                    r = await client.post(
                        f"{base}/sendMessage",
                        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                    )
                elif op == "get_me":
                    r = await client.get(f"{base}/getMe")
                elif op == "get_webhook_info":
                    r = await client.get(f"{base}/getWebhookInfo")
                elif op == "set_webhook":
                    url = _.get("url", "")
                    if not url:
                        return ToolResult(ok=False, error="url required for set_webhook")
                    r = await client.post(f"{base}/setWebhook", json={"url": url})
                elif op == "delete_webhook":
                    r = await client.get(f"{base}/deleteWebhook")
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                data = r.json()
                if data.get("ok"):
                    return ToolResult(ok=True, data=data.get("result", data))
                return ToolResult(ok=False, error=f"Telegram error: {data.get('description', r.text)}")
            except Exception as exc:
                log.exception("telegram_api_request_failed")
                return ToolResult(ok=False, error=f"Telegram communication failed: {exc}")


class InstagramApiTool(Tool):
    name = "instagram_api"
    description = (
        "Interact with Instagram Business API: post media, get insights, "
        "and list comments."
    )

    async def _call(
        self,
        *,
        op: str,
        session: Any = None,
        workspace_id: Any = None,
        media_url: str = "",
        caption: str = "",
        ig_user_id: str = "",
        **_: Any,
    ) -> ToolResult:
        creds = _resolve_creds(session, workspace_id, "instagram_business")
        if not creds:
            return ToolResult(ok=False, error="Instagram Business not connected. Go to Integrations > Instagram Business to connect.")

        token = creds.get("token")
        if not token:
            return ToolResult(ok=False, error="Instagram credentials incomplete.")

        api_version = settings.meta_graph_api_version or "v19.0"
        base = f"https://graph.facebook.com/{api_version}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if op == "post_media":
                    if not ig_user_id or not media_url:
                        return ToolResult(ok=False, error="ig_user_id and media_url required")
                    r = await client.post(
                        f"{base}/{ig_user_id}/media",
                        params={"access_token": token},
                        json={"image_url": media_url, "caption": caption},
                    )
                elif op == "get_insights":
                    if not ig_user_id:
                        return ToolResult(ok=False, error="ig_user_id required")
                    r = await client.get(
                        f"{base}/{ig_user_id}/insights",
                        params={"access_token": token, "metric": "impressions,reach,profile_views"},
                    )
                elif op == "list_media":
                    if not ig_user_id:
                        return ToolResult(ok=False, error="ig_user_id required")
                    r = await client.get(
                        f"{base}/{ig_user_id}/media",
                        params={"access_token": token, "limit": 10},
                    )
                else:
                    return ToolResult(ok=False, error=f"unknown op: {op}")

                if r.status_code in (200, 201):
                    return ToolResult(ok=True, data=r.json())
                return ToolResult(ok=False, error=f"Instagram error {r.status_code}: {r.text}")
            except Exception as exc:
                log.exception("instagram_api_request_failed")
                return ToolResult(ok=False, error=f"Instagram communication failed: {exc}")
