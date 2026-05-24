"""Usage tracking for subscription billing and quotas."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.usage import UsageRecord


async def record_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    model_id: str,
    provider: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float | None = None,
) -> UsageRecord:
    record = UsageRecord(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        model_id=model_id,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
    )
    db.add(record)
    await db.commit()
    return record


async def get_org_usage(
    db: AsyncSession,
    organization_id: uuid.UUID,
    since: datetime | None = None,
) -> dict:
    """Aggregate usage stats for an organization."""
    query = select(
        func.sum(UsageRecord.prompt_tokens).label("total_prompt_tokens"),
        func.sum(UsageRecord.completion_tokens).label("total_completion_tokens"),
        func.sum(UsageRecord.cost_usd).label("total_cost_usd"),
        func.count(UsageRecord.id).label("total_calls"),
    ).where(UsageRecord.organization_id == organization_id)

    if since:
        query = query.where(UsageRecord.created_at >= since)

    result = await db.execute(query)
    row = result.one()

    # Per-model breakdown
    model_query = select(
        UsageRecord.model_id,
        func.sum(UsageRecord.prompt_tokens).label("prompt_tokens"),
        func.sum(UsageRecord.completion_tokens).label("completion_tokens"),
        func.sum(UsageRecord.cost_usd).label("cost_usd"),
        func.count(UsageRecord.id).label("calls"),
    ).where(UsageRecord.organization_id == organization_id)

    if since:
        model_query = model_query.where(UsageRecord.created_at >= since)

    model_query = model_query.group_by(UsageRecord.model_id)
    model_result = await db.execute(model_query)
    models = [dict(r._mapping) for r in model_result.all()]

    return {
        "total_prompt_tokens": row.total_prompt_tokens or 0,
        "total_completion_tokens": row.total_completion_tokens or 0,
        "total_cost_usd": float(row.total_cost_usd) if row.total_cost_usd else 0.0,
        "total_calls": row.total_calls or 0,
        "models": models,
    }
