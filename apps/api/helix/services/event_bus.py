"""Event bus service — matches events to triggers and executes them autonomously."""
from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.models.runtime import Trigger
from helix.services.run_queue import enqueue_run
from helix.workflows.helpers import emit_event

log = get_logger("helix.event_bus")


def evaluate_filter(payload: dict, filter_dict: dict) -> bool:
    """Evaluate custom JSON filters on event payload.
    Supports operators: lt, gt, lte, gte, eq, ne, and exact matching.
    """
    if not filter_dict:
        return True
    for key, condition in filter_dict.items():
        if key not in payload:
            return False
        val = payload[key]
        if isinstance(condition, dict):
            for op, cmp_val in condition.items():
                try:
                    if op == "lt" and not (val < cmp_val):
                        return False
                    elif op == "gt" and not (val > cmp_val):
                        return False
                    elif op == "lte" and not (val <= cmp_val):
                        return False
                    elif op == "gte" and not (val >= cmp_val):
                        return False
                    elif op == "eq" and not (val == cmp_val):
                        return False
                    elif op == "ne" and not (val != cmp_val):
                        return False
                except Exception:
                    return False
        else:
            if val != condition:
                return False
    return True


async def publish_event(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    brand_id: UUID | None,
    event_kind: str,
    payload: dict[str, Any],
) -> int:
    """Publish an event to the internal event bus.

    Checks all enabled triggers in the workspace that match `event_kind`.
    If the filters match and debounce time has elapsed, enqueues the trigger's workflow.
    Returns the number of triggered runs.
    """
    log.info(
        "event_bus.publish",
        workspace_id=str(workspace_id),
        brand_id=str(brand_id) if brand_id else None,
        event_kind=event_kind,
        payload=payload,
    )

    # Query matching enabled triggers
    stmt = select(Trigger).where(
        Trigger.workspace_id == workspace_id,
        Trigger.event_kind == event_kind,
        Trigger.enabled.is_(True),
    )
    if brand_id is not None:
        stmt = stmt.where((Trigger.brand_id == brand_id) | (Trigger.brand_id is None))

    result = await db.execute(stmt)
    triggers = list(result.scalars().all())

    triggered_count = 0
    now = datetime.datetime.now(datetime.UTC)

    for trigger in triggers:
        # Check filter
        if not evaluate_filter(payload, trigger.filter):
            log.info(
                "event_bus.trigger_filter_mismatch",
                trigger_id=str(trigger.id),
                filter=trigger.filter,
            )
            continue

        # Check debounce
        if trigger.last_fired_at and trigger.debounce_s > 0:
            last_fired_utc = trigger.last_fired_at
            if last_fired_utc.tzinfo is None:
                last_fired_utc = last_fired_utc.replace(tzinfo=datetime.UTC)
            elapsed = (now - last_fired_utc).total_seconds()
            if elapsed < trigger.debounce_s:
                log.info(
                    "event_bus.trigger_debounced",
                    trigger_id=str(trigger.id),
                    elapsed=elapsed,
                    debounce=trigger.debounce_s,
                )
                continue

        # Merge inputs_template with event payload
        merged_inputs = {**trigger.inputs_template, **payload}

        log.info(
            "event_bus.trigger_firing",
            trigger_id=str(trigger.id),
            workflow=trigger.workflow,
            brand_id=str(trigger.brand_id or brand_id),
        )

        # Enqueue workflow run
        await enqueue_run(
            brand_id=trigger.brand_id or brand_id,
            workspace_id=trigger.workspace_id,
            workflow=trigger.workflow,
            inputs=merged_inputs,
            config=trigger.config,
            user_id=trigger.created_by,
        )

        # Update trigger statistics
        # Convert now back to naive datetime to match database column type if required
        trigger.last_fired_at = now.replace(tzinfo=None)
        trigger.fire_count += 1
        triggered_count += 1

        # Emit real-time event for UI
        await emit_event(
            run_id=trigger.id,
            kind="event.fired",
            payload={
                "trigger_id": str(trigger.id),
                "trigger_name": trigger.name,
                "event_kind": event_kind,
                "workflow": trigger.workflow,
            },
        )

    if triggered_count > 0:
        await db.commit()

    return triggered_count
