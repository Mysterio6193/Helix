"""Telegram bot webhook + send endpoints.

Flow:
1. User connects their Telegram bot via POST /integrations/telegram/connect/token.
2. They register a webhook pointing at `${api_public_url}/api/v1/telegram/webhook/{workspace_id}`.
3. Incoming Telegram updates are routed through the Helix LLM gateway and a
   reply is sent back via the Bot API.

The `/webhook/{workspace_id}` endpoint is public (Telegram has no way to
present a session cookie), but admin endpoints (`/register-webhook`,
`/send`, `/status`) require an authenticated session and enforce
workspace ACL. All tunables — base URL, system prompt, history length,
TTLs, message size cap — live in `settings`.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import assert_workspace_access
from helix.core.config import get_settings, settings
from helix.core.db import get_db
from helix.core.logging import get_logger
from helix.core.security import decrypt
from helix.core.sessions import require_user
from helix.llm import gateway
from helix.models.organization import User
from helix.models.tool_connection import ToolConnection

log = get_logger("helix.telegram")
router = APIRouter(prefix="/telegram", tags=["telegram"])


def _telegram_api_base() -> str:
    return settings.telegram_api_base.rstrip("/")


def _history_key(chat_id: int) -> str:
    return f"helix:tg:hist:{chat_id}"


def _seen_key(update_id: int) -> str:
    return f"helix:tg:seen:{update_id}"


async def _load_bot_token(db: AsyncSession, workspace_id: uuid.UUID) -> Optional[dict]:
    stmt = select(ToolConnection).where(
        ToolConnection.workspace_id == workspace_id,
        ToolConnection.provider == "telegram",
        ToolConnection.enabled.is_(True),
    )
    conn = (await db.execute(stmt)).scalars().first()
    if conn is None:
        return None
    raw = decrypt(conn.credentials_encrypted)
    creds = json.loads(raw)
    return {"token": creds.get("token"), "connection": conn}


async def _redis():  # lazy import — Redis is optional
    try:
        from helix.core.redis import get_redis  # type: ignore

        return await get_redis()
    except Exception:
        return None


async def _load_history(chat_id: int) -> list[dict]:
    r = await _redis()
    if r is None:
        return []
    try:
        raw = await r.get(_history_key(chat_id))
        if not raw:
            return []
        return json.loads(raw)[-settings.telegram_history_max:]
    except Exception:
        return []


async def _save_history(chat_id: int, history: list[dict]) -> None:
    r = await _redis()
    if r is None:
        return
    try:
        trimmed = history[-settings.telegram_history_max:]
        await r.set(
            _history_key(chat_id),
            json.dumps(trimmed),
            ex=settings.telegram_history_ttl_seconds,
        )
    except Exception:
        pass


async def _was_seen(update_id: int) -> bool:
    r = await _redis()
    if r is None:
        return False
    try:
        set_ok = await r.set(
            _seen_key(update_id),
            "1",
            ex=settings.telegram_dedup_ttl_seconds,
            nx=True,
        )
        return not bool(set_ok)
    except Exception:
        return False


async def _send_telegram(
    token: str, *, chat_id: int, text: str, reply_to: int | None = None
) -> dict:
    cap = settings.telegram_message_max_chars
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text[:cap]}
    if reply_to is not None:
        payload["reply_parameters"] = {"message_id": reply_to}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            f"{_telegram_api_base()}/bot{token}/sendMessage", json=payload
        )
        return r.json()


@router.post("/webhook/{workspace_id}")
async def webhook(
    workspace_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Receives a Telegram update; runs it through the LLM and replies.

    Public (no session) — Telegram's servers can't present a cookie. The
    workspace_id in the URL is non-secret; abuse is mitigated by the fact
    that no reply is sent unless that workspace has a valid bot token
    registered, and by Telegram's own update_id dedup.
    """
    body = await request.json()
    update_id = body.get("update_id")
    if update_id and await _was_seen(int(update_id)):
        return {"ok": True, "dedup": True}

    msg = body.get("message") or body.get("edited_message") or {}
    text = (msg.get("text") or "").strip()
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    sender = msg.get("from") or {}

    if not chat_id or not text:
        return {"ok": True, "ignored": "no_text"}

    creds = await _load_bot_token(db, workspace_id)
    if creds is None or not creds["token"]:
        log.warning("telegram.webhook_no_token", workspace_id=str(workspace_id))
        return {"ok": True, "ignored": "no_bot"}

    # Slash commands
    if text.startswith("/"):
        cmd = text.split()[0].lower()
        if cmd in ("/start", "/help"):
            await _send_telegram(
                creds["token"],
                chat_id=chat_id,
                text=(
                    "Hi, I'm Helix. Send a message and I'll respond.\n\n"
                    "Commands:\n"
                    "/reset – clear our conversation\n"
                    "/help – this message"
                ),
            )
            return {"ok": True}
        if cmd == "/reset":
            await _save_history(int(chat_id), [])
            await _send_telegram(creds["token"], chat_id=chat_id, text="Conversation cleared.")
            return {"ok": True}

    history = await _load_history(int(chat_id))
    messages = history + [{"role": "user", "content": text}]
    try:
        result = await gateway.complete(
            messages=messages,
            system=settings.telegram_system_prompt,
            max_tokens=600,
        )
        reply_text = (result.content or "").strip() or "…"
    except Exception as exc:  # noqa: BLE001
        log.exception("telegram.llm_failed", chat_id=chat_id)
        reply_text = (
            "Sorry — I hit an issue generating a reply. "
            f"({type(exc).__name__})"
        )

    await _send_telegram(
        creds["token"],
        chat_id=int(chat_id),
        text=reply_text,
        reply_to=msg.get("message_id"),
    )
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply_text})
    await _save_history(int(chat_id), history)

    log.info(
        "telegram.replied",
        chat_id=chat_id,
        user=sender.get("username"),
        in_chars=len(text),
        out_chars=len(reply_text),
    )
    return {"ok": True}


class RegisterWebhook(BaseModel):
    workspace_id: uuid.UUID
    url: str | None = None  # override; defaults to api_public_url


@router.post("/register-webhook")
async def register_webhook(
    payload: RegisterWebhook,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Tell Telegram where to deliver updates. Run once after connecting."""
    await assert_workspace_access(db, user, payload.workspace_id)

    creds = await _load_bot_token(db, payload.workspace_id)
    if creds is None:
        raise HTTPException(status_code=404, detail="telegram_not_connected")
    s = get_settings()
    base = (payload.url or s.api_public_url).rstrip("/")
    webhook_url = f"{base}/api/v1/telegram/webhook/{payload.workspace_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{_telegram_api_base()}/bot{creds['token']}/setWebhook",
            json={"url": webhook_url, "allowed_updates": ["message", "edited_message"]},
        )
        data = r.json()
    return {"ok": data.get("ok", False), "webhook_url": webhook_url, "response": data}


class SendMessage(BaseModel):
    workspace_id: uuid.UUID
    chat_id: int
    text: str


@router.post("/send")
async def send(
    payload: SendMessage,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually send a Telegram message from Helix."""
    await assert_workspace_access(db, user, payload.workspace_id)

    creds = await _load_bot_token(db, payload.workspace_id)
    if creds is None:
        raise HTTPException(status_code=404, detail="telegram_not_connected")
    resp = await _send_telegram(
        creds["token"], chat_id=payload.chat_id, text=payload.text
    )
    return {"ok": resp.get("ok", False), "response": resp}


@router.get("/status")
async def status_endpoint(
    workspace_id: uuid.UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns bot identity + webhook info if connected."""
    await assert_workspace_access(db, user, workspace_id)

    creds = await _load_bot_token(db, workspace_id)
    if creds is None:
        return {"connected": False}
    base = _telegram_api_base()
    async with httpx.AsyncClient(timeout=10.0) as client:
        me_r = await client.get(f"{base}/bot{creds['token']}/getMe")
        wh_r = await client.get(f"{base}/bot{creds['token']}/getWebhookInfo")
    return {
        "connected": True,
        "bot": me_r.json().get("result") if me_r.status_code == 200 else None,
        "webhook": wh_r.json().get("result") if wh_r.status_code == 200 else None,
    }
