"""Workflow-run queue service — enqueues jobs onto Redis for the worker."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select

from helix.core.config import get_settings
from helix.core.db import session_factory
from helix.core.logging import get_logger
from helix.models.workflow import WorkflowRun

log = get_logger(__name__)


def _queue_key() -> str:
    return get_settings().run_queue_key


def _idempotency_ttl() -> int:
    return get_settings().run_idempotency_ttl_seconds


def _idem_redis_key(workspace_id: UUID, key: str) -> str:
    return f"{_queue_key()}:idem:{workspace_id}:{key}"


async def enqueue_run(
    *,
    brand_id: UUID,
    workspace_id: UUID,
    workflow: str,
    inputs: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    user_id: UUID | None = None,
    idempotency_key: str | None = None,
) -> WorkflowRun:
    """Create a `WorkflowRun` row and push a job onto the Redis queue.

    When `idempotency_key` is set, a second call with the same key for the same
    workspace within the TTL returns the previously-created `WorkflowRun`
    without re-enqueueing.
    """
    settings = get_settings()
    client = redis.from_url(settings.redis_url, decode_responses=True)

    try:
        # Idempotency check — claim the key atomically. If we lose the race,
        # return the existing run.
        if idempotency_key:
            existing_run_id = await client.get(_idem_redis_key(workspace_id, idempotency_key))
            if existing_run_id:
                async with session_factory() as session:
                    existing = await session.get(WorkflowRun, UUID(existing_run_id))
                    if existing is not None:
                        log.info(
                            "run.idempotent_hit",
                            run_id=existing_run_id,
                            workflow=workflow,
                        )
                        return existing

        async with session_factory() as session:
            run = WorkflowRun(
                brand_id=brand_id,
                workspace_id=workspace_id,
                workflow=workflow,
                status="queued",
                inputs=inputs or {},
                config=config or {},
                created_by=user_id,
                idempotency_key=idempotency_key,
            )
            session.add(run)
            await session.flush()
            await session.commit()
            run_id = run.id

        if idempotency_key:
            # SETNX so a concurrent caller with the same key sees us — if we
            # lose, fall back to the existing row.
            claimed = await client.set(
                _idem_redis_key(workspace_id, idempotency_key),
                str(run_id),
                nx=True,
                ex=_idempotency_ttl(),
            )
            if not claimed:
                holder = await client.get(_idem_redis_key(workspace_id, idempotency_key))
                if holder and holder != str(run_id):
                    async with session_factory() as session:
                        result = await session.execute(
                            select(WorkflowRun).where(WorkflowRun.id == UUID(holder))
                        )
                        existing = result.scalar_one_or_none()
                        if existing is not None:
                            log.info(
                                "run.idempotent_loser",
                                run_id=str(existing.id),
                                workflow=workflow,
                            )
                            return existing

        payload = {
            "run_id": str(run_id),
            "brand_id": str(brand_id),
            "workspace_id": str(workspace_id),
            "workflow": workflow,
            "inputs": inputs or {},
            "config": config or {},
            "user_id": str(user_id) if user_id else None,
            "retries": 0,
            "idempotency_key": idempotency_key,
        }
        await client.rpush(_queue_key(), json.dumps(payload))
        log.info("run.enqueued", run_id=str(run_id), workflow=workflow)
    finally:
        await client.aclose()

    async with session_factory() as session:
        return await session.get(WorkflowRun, run_id)  # type: ignore[return-value]
