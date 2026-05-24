"""Seed intelligence data for testing."""
import asyncio
from datetime import datetime, timedelta

from helix.core.db import AsyncSessionLocal
from helix.models.browser import BrowserAutomation, BrowserSession
from helix.models.generation import MediaGenerationJob
from helix.models.intelligence import (
    CustomerSegment,
    Experiment,
    ExperimentEvent,
    IntelligenceSignal,
    PerformanceSnapshot,
)
from helix.models.organization import Workspace


async def seed():
    async with AsyncSessionLocal() as session:
        # Get first workspace
        from sqlalchemy import select
        result = await session.execute(select(Workspace).limit(1))
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            return


        # Create customer segments
        segments = [
            {"key": "champions", "name": "Champions", "count": 245, "ltv": 450.0, "aov": 85.0},
            {"key": "loyal", "name": "Loyal Customers", "count": 512, "ltv": 320.0, "aov": 65.0},
            {"key": "new", "name": "New Customers", "count": 89, "ltv": 45.0, "aov": 32.0},
            {"key": "at_risk", "name": "At Risk", "count": 1204, "ltv": 180.0, "aov": 42.0, "churn": 0.68},
            {"key": "hibernating", "name": "Hibernating", "count": 340, "ltv": 120.0, "aov": 38.0},
        ]

        for seg_data in segments:
            existing = await session.execute(
                select(CustomerSegment)
                .where(
                    CustomerSegment.workspace_id == workspace.id,
                    CustomerSegment.segment_key == seg_data["key"],
                )
            )
            if not existing.scalar_one_or_none():
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

        # Generate mock performance data
        import random
        platforms = ["meta_ads", "shopify", "stripe"]
        metrics = {
            "meta_ads": ["spend", "impressions", "clicks", "ctr", "conversions", "roas"],
            "shopify": ["revenue", "orders", "items"],
            "stripe": ["balance"],
        }

        base_date = datetime.utcnow() - timedelta(days=30)
        count = 0

        for day in range(30):
            date = base_date + timedelta(days=day)
            for platform in platforms:
                for metric in metrics[platform]:
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
                    count += 1

        # Create some intelligence signals
        signals = [
            {
                "layer": "revenue",
                "type": "anomaly",
                "severity": "warning",
                "title": "Revenue Spike Detected",
                "description": "Daily revenue increased 35% above average. Review campaign performance.",
                "action": "Analyze which campaign drove the spike and scale budget.",
            },
            {
                "layer": "campaign",
                "type": "anomaly",
                "severity": "critical",
                "title": "ROAS Below Target",
                "description": "Meta Ads ROAS dropped to 1.8x, below 2.5x target.",
                "action": "Pause underperforming ad sets and refresh creatives.",
            },
            {
                "layer": "creative",
                "type": "trend",
                "severity": "warning",
                "title": "Creative Fatigue Detected",
                "description": "CTR declined 28% over 7 days on hero creative.",
                "action": "Generate 3 new variants and launch A/B test.",
            },
            {
                "layer": "customer",
                "type": "opportunity",
                "severity": "info",
                "title": "VIP Segment Growing",
                "description": "Champions segment increased 12% this month.",
                "action": "Launch exclusive loyalty offer for VIP customers.",
            },
        ]

        for sig_data in signals:
            signal = IntelligenceSignal(
                workspace_id=workspace.id,
                layer=sig_data["layer"],
                signal_type=sig_data["type"],
                severity=sig_data["severity"],
                title=sig_data["title"],
                description=sig_data["description"],
                source_data={},
                recommended_action=sig_data["action"],
                auto_triggered=True,
            )
            session.add(signal)

        # Create browser automation templates
        automations = [
            {
                "name": "Meta Ads Creative Refresh",
                "description": "Automatically refresh Meta Ads creatives when fatigue is detected",
                "target_site": "meta_ads",
                "action": "create_campaign",
                "config": {"budget": 50, "objective": "conversions"},
            },
            {
                "name": "Shopify Price Monitor",
                "description": "Monitor competitor prices and adjust Shopify pricing",
                "target_site": "shopify",
                "action": "edit_product",
                "config": {"price_adjustment": -0.05},
            },
            {
                "name": "Canva Asset Sync",
                "description": "Sync generated assets to Canva for design team",
                "target_site": "canva",
                "action": "upload_asset",
                "config": {"folder": "Helix Generated"},
            },
        ]

        for auto_data in automations:
            existing = await session.execute(
                select(BrowserAutomation)
                .where(
                    BrowserAutomation.workspace_id == workspace.id,
                    BrowserAutomation.name == auto_data["name"],
                )
            )
            if not existing.scalar_one_or_none():
                automation = BrowserAutomation(
                    workspace_id=workspace.id,
                    name=auto_data["name"],
                    description=auto_data["description"],
                    target_site=auto_data["target_site"],
                    action=auto_data["action"],
                    config=auto_data["config"],
                )
                session.add(automation)

        # Create a browser session
        existing_session = await session.execute(
            select(BrowserSession)
            .where(BrowserSession.workspace_id == workspace.id)
            .limit(1)
        )
        if not existing_session.scalar_one_or_none():
            browser_session = BrowserSession(
                workspace_id=workspace.id,
                name="Main Automation Session",
                provider="local",
                status="idle",
                target_url="https://business.facebook.com",
                config={"headless": True, "viewport": {"width": 1920, "height": 1080}},
            )
            session.add(browser_session)

        # Create a sample media generation job
        existing_job = await session.execute(
            select(MediaGenerationJob)
            .where(MediaGenerationJob.workspace_id == workspace.id)
            .limit(1)
        )
        if not existing_job.scalar_one_or_none():
            media_job = MediaGenerationJob(
                workspace_id=workspace.id,
                name="Sample Creative Batch",
                job_type="image",
                status="completed",
                model="image:gpt-image-1",
                prompts=[
                    "Professional product photography on white background",
                    "Lifestyle shot in modern kitchen setting",
                    "Close-up detail shot with dramatic lighting",
                ],
                config={"size": "1024x1024", "quality": "high"},
                results=[
                    {"type": "image", "prompt": "Professional product photography on white background", "s3_key": "generated/media/sample_1.png", "status": "success"},
                    {"type": "image", "prompt": "Lifestyle shot in modern kitchen setting", "s3_key": "generated/media/sample_2.png", "status": "success"},
                    {"type": "image", "prompt": "Close-up detail shot with dramatic lighting", "s3_key": "generated/media/sample_3.png", "status": "success"},
                ],
                total_items=3,
                completed_items=3,
                failed_items=0,
                total_cost_usd=0.12,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            session.add(media_job)

        # Create a sample A/B experiment
        existing_exp = await session.execute(
            select(Experiment)
            .where(Experiment.workspace_id == workspace.id)
            .limit(1)
        )
        if not existing_exp.scalar_one_or_none():
            experiment = Experiment(
                workspace_id=workspace.id,
                name="Hero Image A/B Test",
                hypothesis="Lifestyle hero image will convert 15% better than product-only",
                experiment_type="ab",
                primary_metric="conversion_rate",
                traffic_allocation=100,
                variants=[
                    {"id": "control", "name": "Product Only", "traffic_pct": 50, "config": {"image": "product_white_bg"}},
                    {"id": "lifestyle", "name": "Lifestyle", "traffic_pct": 50, "config": {"image": "lifestyle_kitchen"}},
                ],
                control_variant_id="control",
                min_confidence=0.95,
                min_sample_size=100,
                auto_stop=True,
                status="running",
                started_at=datetime.utcnow(),
            )
            session.add(experiment)
            await session.flush()

            # Generate realistic experiment events
            import random
            random.seed(42)

            # Simulate 500 impressions per variant with different conversion rates
            for variant_id in ["control", "lifestyle"]:
                # Control: 2.1% conversion rate
                # Lifestyle: 2.8% conversion rate (33% uplift)
                conversion_rate = 0.021 if variant_id == "control" else 0.028
                ctr = 0.045 if variant_id == "control" else 0.058

                for i in range(500):
                    # Impression
                    session.add(ExperimentEvent(
                        experiment_id=experiment.id,
                        variant_id=variant_id,
                        event_type="impression",
                        session_id=f"session_{variant_id}_{i}",
                    ))

                    # Conversion (probabilistic)
                    if random.random() < conversion_rate:
                        session.add(ExperimentEvent(
                            experiment_id=experiment.id,
                            variant_id=variant_id,
                            event_type="conversion",
                            session_id=f"session_{variant_id}_{i}",
                        ))

                    # Click (probabilistic)
                    if random.random() < ctr:
                        session.add(ExperimentEvent(
                            experiment_id=experiment.id,
                            variant_id=variant_id,
                            event_type="click",
                            session_id=f"session_{variant_id}_{i}",
                        ))

                    # Revenue (for conversions)
                    if random.random() < conversion_rate * 0.8:  # 80% of conversions have revenue
                        session.add(ExperimentEvent(
                            experiment_id=experiment.id,
                            variant_id=variant_id,
                            event_type="revenue",
                            value=round(random.gauss(65, 20), 2),
                            session_id=f"session_{variant_id}_{i}",
                        ))

        # Create an MVT experiment
        existing_mvt = await session.execute(
            select(Experiment)
            .where(
                Experiment.workspace_id == workspace.id,
                Experiment.experiment_type == "mvt",
            )
            .limit(1)
        )
        if not existing_mvt.scalar_one_or_none():
            factors = {
                "headline": {
                    "levels": [
                        {"value": "Great Deals", "config": {"text": "Great Deals Await"}},
                        {"value": "Limited Time", "config": {"text": "Limited Time Offer"}},
                    ]
                },
                "image": {
                    "levels": [
                        {"value": "Product", "config": {"image": "product_white"}},
                        {"value": "Lifestyle", "config": {"image": "lifestyle_kitchen"}},
                    ]
                },
            }
            mvt_variants = [
                {"id": "mvt_0", "name": "Great Deals / Product", "traffic_pct": 25, "config": {"text": "Great Deals Await", "image": "product_white"}, "factor_levels": {"headline": "Great Deals", "image": "Product"}},
                {"id": "mvt_1", "name": "Great Deals / Lifestyle", "traffic_pct": 25, "config": {"text": "Great Deals Await", "image": "lifestyle_kitchen"}, "factor_levels": {"headline": "Great Deals", "image": "Lifestyle"}},
                {"id": "mvt_2", "name": "Limited Time / Product", "traffic_pct": 25, "config": {"text": "Limited Time Offer", "image": "product_white"}, "factor_levels": {"headline": "Limited Time", "image": "Product"}},
                {"id": "mvt_3", "name": "Limited Time / Lifestyle", "traffic_pct": 25, "config": {"text": "Limited Time Offer", "image": "lifestyle_kitchen"}, "factor_levels": {"headline": "Limited Time", "image": "Lifestyle"}},
            ]

            mvt_exp = Experiment(
                workspace_id=workspace.id,
                name="MVT: Headline × Image",
                hypothesis="Lifestyle imagery with limited-time messaging drives highest conversion",
                experiment_type="mvt",
                primary_metric="conversion_rate",
                traffic_allocation=100,
                variants=mvt_variants,
                control_variant_id="mvt_0",
                factors=factors,
                min_confidence=0.95,
                min_sample_size=50,
                auto_stop=True,
                status="running",
                started_at=datetime.utcnow(),
            )
            session.add(mvt_exp)
            await session.flush()

            # Generate events for MVT experiment
            import random
            random.seed(99)
            conv_rates = {
                "mvt_0": 0.020,
                "mvt_1": 0.032,
                "mvt_2": 0.018,
                "mvt_3": 0.028,
            }
            ctr_rates = {
                "mvt_0": 0.040,
                "mvt_1": 0.055,
                "mvt_2": 0.035,
                "mvt_3": 0.050,
            }
            for vid, cr in conv_rates.items():
                ctr = ctr_rates[vid]
                for i in range(300):
                    session.add(ExperimentEvent(
                        experiment_id=mvt_exp.id,
                        variant_id=vid,
                        event_type="impression",
                        session_id=f"mvt_{vid}_{i}",
                    ))
                    if random.random() < cr:
                        session.add(ExperimentEvent(
                            experiment_id=mvt_exp.id,
                            variant_id=vid,
                            event_type="conversion",
                            session_id=f"mvt_{vid}_{i}",
                        ))
                    if random.random() < ctr:
                        session.add(ExperimentEvent(
                            experiment_id=mvt_exp.id,
                            variant_id=vid,
                            event_type="click",
                            session_id=f"mvt_{vid}_{i}",
                        ))
                    if random.random() < cr * 0.7:
                        session.add(ExperimentEvent(
                            experiment_id=mvt_exp.id,
                            variant_id=vid,
                            event_type="revenue",
                            value=round(random.gauss(60, 15), 2),
                            session_id=f"mvt_{vid}_{i}",
                        ))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
