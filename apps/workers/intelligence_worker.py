"""Background intelligence signal generator.

This worker periodically analyzes data and generates intelligence signals
that appear in the dashboard and trigger autonomous actions.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.db import AsyncSessionLocal
from helix.core.logging import get_logger
from helix.models.intelligence import (
    PerformanceSnapshot,
    IntelligenceSignal,
    CustomerSegment,
    CompetitorSnapshot,
)
from helix.intelligence.analysis import detect_anomaly, simple_forecast

log = get_logger(__name__)


async def generate_mock_performance_data(session: AsyncSession):
    """Generate mock performance data for testing."""
    # Get a workspace
    from helix.models.organization import Workspace
    result = await session.execute(
        select(Workspace).limit(1)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        return

    # Generate some mock data points
    platforms = ["meta_ads", "shopify", "stripe"]
    metrics = {
        "meta_ads": ["spend", "impressions", "clicks", "ctr", "conversions", "roas"],
        "shopify": ["revenue", "orders", "items"],
        "stripe": ["balance"],
    }

    base_date = datetime.utcnow() - timedelta(days=30)

    for day in range(30):
        date = base_date + timedelta(days=day)
        for platform in platforms:
            for metric in metrics[platform]:
                # Generate realistic values
                if metric == "revenue":
                    value = 500 + random.gauss(0, 100) + day * 10
                elif metric == "roas":
                    value = 2.5 + random.gauss(0, 0.5)
                elif metric == "ctr":
                    value = 1.5 + random.gauss(0, 0.3)
                elif metric == "spend":
                    value = 200 + random.gauss(0, 50)
                elif metric == "orders":
                    value = 20 + random.gauss(0, 5) + day * 0.5
                else:
                    value = random.gauss(100, 20)

                snap = PerformanceSnapshot(
                    workspace_id=workspace.id,
                    platform=platform,
                    metric_type=metric,
                    value=max(0, value),
                    currency="USD" if metric in ["revenue", "spend", "balance"] else None,
                    captured_at=date,
                )
                session.add(snap)

    await session.commit()
    log.info("generated_mock_performance_data", workspace_id=str(workspace.id))


async def generate_intelligence_signals(session: AsyncSession):
    """Generate intelligence signals from data analysis."""
    from helix.models.organization import Workspace
    result = await session.execute(
        select(Workspace).limit(1)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        return

    # Check for anomalies in recent data
    cutoff = datetime.utcnow() - timedelta(days=7)
    from helix.models.intelligence import PerformanceSnapshot

    result = await session.execute(
        select(PerformanceSnapshot)
        .where(
            PerformanceSnapshot.workspace_id == workspace.id,
            PerformanceSnapshot.metric_type == "revenue",
            PerformanceSnapshot.captured_at >= cutoff,
        )
        .order_by(PerformanceSnapshot.captured_at)
    )
    snapshots = result.scalars().all()

    if len(snapshots) > 7:
        values = [s.value for s in snapshots]
        anomaly_indices = detect_anomaly(values)

        for idx in anomaly_indices:
            if idx < len(snapshots):
                snap = snapshots[idx]
                # Check if signal already exists
                existing = await session.execute(
                    select(IntelligenceSignal)
                    .where(
                        IntelligenceSignal.workspace_id == workspace.id,
                        IntelligenceSignal.layer == "revenue",
                        IntelligenceSignal.title.like(f"%Revenue Anomaly%"),
                        IntelligenceSignal.created_at >= datetime.utcnow() - timedelta(hours=24),
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                signal = IntelligenceSignal(
                    workspace_id=workspace.id,
                    layer="revenue",
                    signal_type="anomaly",
                    severity="warning",
                    title=f"Revenue Anomaly Detected",
                    description=f"Unusual revenue pattern on {snap.captured_at.strftime('%Y-%m-%d')}: ${snap.value:.2f}",
                    source_data={"value": snap.value, "date": snap.captured_at.isoformat()},
                    recommended_action="Review campaign performance and check for external factors",
                    auto_triggered=True,
                )
                session.add(signal)

        await session.commit()


async def seed_customer_segments(session: AsyncSession):
    """Create default customer segments."""
    from helix.models.organization import Workspace
    result = await session.execute(
        select(Workspace).limit(1)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        return

    segments = [
        {"key": "champions", "name": "Champions", "count": 245, "ltv": 450, "aov": 85},
        {"key": "loyal", "name": "Loyal Customers", "count": 512, "ltv": 320, "aov": 65},
        {"key": "new", "name": "New Customers", "count": 89, "ltv": 45, "aov": 32},
        {"key": "at_risk", "name": "At Risk", "count": 1204, "ltv": 180, "aov": 42, "churn": 0.68},
        {"key": "hibernating", "name": "Hibernating", "count": 340, "ltv": 120, "aov": 38},
    ]

    for seg_data in segments:
        existing = await session.execute(
            select(CustomerSegment)
            .where(
                CustomerSegment.workspace_id == workspace.id,
                CustomerSegment.segment_key == seg_data["key"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        segment = CustomerSegment(
            workspace_id=workspace.id,
            segment_key=seg_data["key"],
            name=seg_data["name"],
            member_count=seg_data["count"],
            avg_ltv=seg_data.get("ltv"),
            avg_order_value=seg_data.get("aov"),
            churn_rate=seg_data.get("churn"),
            computed_at=datetime.utcnow(),
        )
        session.add(segment)

    await session.commit()


async def run_intelligence_worker():
    """Main worker loop."""
    log.info("intelligence_worker_started")

    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Seed data if needed
                await seed_customer_segments(session)

                # Generate mock data (only if no data exists)
                result = await session.execute(
                    select(PerformanceSnapshot).limit(1)
                )
                if not result.scalar_one_or_none():
                    await generate_mock_performance_data(session)

                # Generate signals
                await generate_intelligence_signals(session)

        except Exception as e:
            log.error("intelligence_worker_error", error=str(e))

        # Run every 5 minutes
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(run_intelligence_worker())
