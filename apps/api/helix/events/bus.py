"""Event bus: Redis pubsub for live streaming + Postgres event_log for replay."""
from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.redis import get_redis
from helix.models.event import Event


def channel_for_run(run_id: uuid.UUID | str) -> str:
    return f"run:{run_id}"


def channel_for_brand(brand_id: uuid.UUID | str) -> str:
    return f"brand:{brand_id}"


def channel_for_workspace(workspace_id: uuid.UUID | str) -> str:
    return f"workspace:{workspace_id}"


def _json_default(obj: Any) -> Any:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


async def publish(
    db: AsyncSession | None,
    *,
    kind: str,
    channel: str,
    payload: dict[str, Any],
    workspace_id: uuid.UUID | None = None,
    brand_id: uuid.UUID | None = None,
    workflow_run_id: uuid.UUID | None = None,
    persist: bool = True,
) -> None:
    """Publish to Redis pubsub and (optionally) persist to events table."""
    enriched = {
        **payload,
        "kind": kind,
        "channel": channel,
        "ts": datetime.now(UTC).isoformat(),
    }
    body = json.dumps(enriched, default=_json_default)

    redis = await get_redis()
    await redis.publish(channel, body)

    if persist and db is not None:
        event = Event(
            workspace_id=workspace_id,
            brand_id=brand_id,
            workflow_run_id=workflow_run_id,
            kind=kind,
            channel=channel,
            payload=payload,
        )
        db.add(event)
        await db.flush()


async def subscribe(channel: str) -> AsyncIterator[dict[str, Any]]:
    """Async iterator yielding decoded events from a Redis pubsub channel."""
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message is None:
                continue
            if message.get("type") != "message":
                continue
            data = message.get("data")
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            try:
                yield json.loads(data)
            except (TypeError, ValueError):
                yield {"raw": data}
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
