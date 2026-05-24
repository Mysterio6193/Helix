"""Scratch verification script for the Event Bus trigger matching and filter evaluation."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.runtime import Trigger
from helix.services.event_bus import evaluate_filter, publish_event


def test_filters():
    # 1. Exact match
    assert evaluate_filter({"roas": 2.5, "ctr": 1.2}, {"roas": 2.5}) is True
    assert evaluate_filter({"roas": 2.5, "ctr": 1.2}, {"roas": 3.0}) is False
    assert evaluate_filter({"roas": 2.5, "ctr": 1.2}, {"non_existent": 1.0}) is False

    # 2. Operators: lt, gt
    assert evaluate_filter({"roas": 1.5}, {"roas": {"lt": 2.0}}) is True
    assert evaluate_filter({"roas": 2.5}, {"roas": {"lt": 2.0}}) is False
    assert evaluate_filter({"roas": 2.5}, {"roas": {"gt": 2.0}}) is True

    # 3. Operators: lte, gte
    assert evaluate_filter({"roas": 2.0}, {"roas": {"lte": 2.0}}) is True
    assert evaluate_filter({"roas": 2.0}, {"roas": {"gte": 2.0}}) is True

    # 4. Operators: eq, ne
    assert evaluate_filter({"roas": 2.0}, {"roas": {"eq": 2.0}}) is True
    assert evaluate_filter({"roas": 2.0}, {"roas": {"ne": 2.0}}) is False
    assert evaluate_filter({"roas": 2.0}, {"roas": {"ne": 3.0}}) is True



async def test_publish_event():
    # Mock DB Session
    db_mock = MagicMock(spec=AsyncSession)
    db_mock.execute = AsyncMock()
    db_mock.commit = AsyncMock()

    workspace_id = uuid4()
    brand_id = uuid4()

    # Create dummy trigger matching fatigue event
    trigger = Trigger(
        id=uuid4(),
        workspace_id=workspace_id,
        brand_id=brand_id,
        name="Campaign Fatigue Auto-Refresh",
        event_kind="campaign_fatigue_detected",
        filter={"fatigue_score": {"gt": 0.80}},
        workflow="executive_council",
        inputs_template={"target_budget_daily": 200},
        enabled=True,
        debounce_s=60,
        last_fired_at=None,
        fire_count=0
    )

    # Mock DB select triggers execution return
    mock_result = MagicMock()
    mock_result.scalars = MagicMock()
    mock_result.scalars.return_value.all = MagicMock(return_value=[trigger])
    db_mock.execute.return_value = mock_result

    # Mock enqueue_run in context
    import helix.services.event_bus
    original_enqueue = helix.services.event_bus.enqueue_run
    
    enqueue_called = []
    async def mock_enqueue(*args, **kwargs):
        enqueue_called.append(kwargs)
        mock_run = MagicMock()
        mock_run.id = uuid4()
        return mock_run

    helix.services.event_bus.enqueue_run = mock_enqueue

    try:
        # Publish matching event
        count = await publish_event(
            db_mock,
            workspace_id=workspace_id,
            brand_id=brand_id,
            event_kind="campaign_fatigue_detected",
            payload={"fatigue_score": 0.85, "spend": 500}
        )

        assert count == 1, f"Expected 1 trigger firing, got {count}"
        assert len(enqueue_called) == 1, "enqueue_run should be called exactly once"
        assert enqueue_called[0]["inputs"]["target_budget_daily"] == 200, "Inputs template should merge correctly"
        assert enqueue_called[0]["inputs"]["fatigue_score"] == 0.85, "Payload variables should merge correctly"
        assert trigger.fire_count == 1, "Fire count should increment"
        assert trigger.last_fired_at is not None, "Last fired timestamp should be set"
        

        # Publish non-matching event (fails filter)
        trigger.fire_count = 0
        trigger.last_fired_at = None
        enqueue_called.clear()

        count_miss = await publish_event(
            db_mock,
            workspace_id=workspace_id,
            brand_id=brand_id,
            event_kind="campaign_fatigue_detected",
            payload={"fatigue_score": 0.70, "spend": 500}
        )

        assert count_miss == 0, f"Expected 0 trigger firings (filter mismatch), got {count_miss}"
        assert len(enqueue_called) == 0, "enqueue_run should not be called"
        

    finally:
        helix.services.event_bus.enqueue_run = original_enqueue


if __name__ == "__main__":
    test_filters()
    asyncio.run(test_publish_event())
