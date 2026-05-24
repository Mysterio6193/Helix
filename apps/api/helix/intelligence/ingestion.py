"""Intelligence layer ingestion adapters."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.models.intelligence import PerformanceSnapshot
from helix.tools.adapters.saas import MetaAdsApiTool, ShopifyApiTool, StripeApiTool

log = get_logger(__name__)


class MetaAdsIngestion:
    """Ingest performance metrics from Meta Ads API."""

    def __init__(self, tool: MetaAdsApiTool):
        self.tool = tool

    async def fetch_daily_metrics(
        self,
        db: AsyncSession,
        workspace_id: Any,
        brand_id: Any,
        days: int = 30,
    ) -> list[PerformanceSnapshot]:
        """Fetch campaign insights and store as performance snapshots."""
        end_date = datetime.utcnow()
        end_date - timedelta(days=days)

        try:
            # Fetch campaign insights
            insights = await self.tool.get_campaign_insights(
                date_preset=f"last_{days}d"
            )

            snapshots = []
            for day_data in insights.get("data", []):
                date_str = day_data.get("date_start", "")
                captured_at = datetime.strptime(date_str, "%Y-%m-%d") if date_str else end_date

                # Create snapshots for each metric
                metrics = {
                    "spend": float(day_data.get("spend", 0) or 0),
                    "impressions": int(day_data.get("impressions", 0) or 0),
                    "clicks": int(day_data.get("clicks", 0) or 0),
                    "ctr": float(day_data.get("ctr", 0) or 0),
                    "cpc": float(day_data.get("cpc", 0) or 0),
                    "conversions": int(day_data.get("conversions", 0) or 0),
                    "purchase_value": float(day_data.get("purchase_roas", [{}])[0].get("value", 0) or 0),
                }

                for metric_type, value in metrics.items():
                    snapshots.append(PerformanceSnapshot(
                        workspace_id=workspace_id,
                        brand_id=brand_id,
                        platform="meta_ads",
                        metric_type=metric_type,
                        value=value,
                        currency="USD",
                        metadata_={"raw": day_data},
                        captured_at=captured_at,
                    ))

            return snapshots

        except Exception as e:
            log.error("meta_ads_ingestion_failed", error=str(e))
            return []


class ShopifyIngestion:
    """Ingest revenue and order metrics from Shopify."""

    def __init__(self, tool: ShopifyApiTool):
        self.tool = tool

    async def fetch_daily_metrics(
        self,
        db: AsyncSession,
        workspace_id: Any,
        brand_id: Any,
        days: int = 30,
    ) -> list[PerformanceSnapshot]:
        """Fetch orders and compute daily metrics."""
        try:
            orders = await self.tool.list_orders(limit=250)

            # Group by day
            daily: dict[str, dict[str, float]] = {}
            for order in orders:
                created_at = order.get("created_at", "")
                if not created_at:
                    continue
                date_key = created_at[:10]  # YYYY-MM-DD

                if date_key not in daily:
                    daily[date_key] = {"revenue": 0.0, "orders": 0, "items": 0}

                daily[date_key]["revenue"] += float(order.get("total_price", 0) or 0)
                daily[date_key]["orders"] += 1
                daily[date_key]["items"] += len(order.get("line_items", []))

            snapshots = []
            for date_key, data in daily.items():
                captured_at = datetime.strptime(date_key, "%Y-%m-%d")
                for metric_type, value in data.items():
                    snapshots.append(PerformanceSnapshot(
                        workspace_id=workspace_id,
                        brand_id=brand_id,
                        platform="shopify",
                        metric_type=metric_type,
                        value=value,
                        currency="USD",
                        metadata_={},
                        captured_at=captured_at,
                    ))

            return snapshots

        except Exception as e:
            log.error("shopify_ingestion_failed", error=str(e))
            return []


class StripeIngestion:
    """Ingest revenue metrics from Stripe."""

    def __init__(self, tool: StripeApiTool):
        self.tool = tool

    async def fetch_daily_metrics(
        self,
        db: AsyncSession,
        workspace_id: Any,
        brand_id: Any,
        days: int = 30,
    ) -> list[PerformanceSnapshot]:
        """Fetch charges and compute daily revenue."""
        try:
            # Get balance to verify connection
            balance = await self.tool.get_balance()

            snapshots = []
            # For now, just store the available balance
            for item in balance.get("available", []):
                snapshots.append(PerformanceSnapshot(
                    workspace_id=workspace_id,
                    brand_id=brand_id,
                    platform="stripe",
                    metric_type="balance",
                    value=float(item.get("amount", 0)) / 100,  # Stripe uses cents
                    currency=item.get("currency", "USD").upper(),
                    metadata_={"balance": balance},
                    captured_at=datetime.utcnow(),
                ))

            return snapshots

        except Exception as e:
            log.error("stripe_ingestion_failed", error=str(e))
            return []


async def run_full_sync(
    db: AsyncSession,
    workspace_id: Any,
    brand_id: Any,
    integrations: dict[str, Any],
) -> dict[str, int]:
    """Run full sync across all connected platforms."""
    results = {}

    if "meta_ads" in integrations:
        meta = MetaAdsIngestion(integrations["meta_ads"])
        snapshots = await meta.fetch_daily_metrics(db, workspace_id, brand_id)
        for snap in snapshots:
            db.add(snap)
        results["meta_ads"] = len(snapshots)

    if "shopify" in integrations:
        shopify = ShopifyIngestion(integrations["shopify"])
        snapshots = await shopify.fetch_daily_metrics(db, workspace_id, brand_id)
        for snap in snapshots:
            db.add(snap)
        results["shopify"] = len(snapshots)

    if "stripe" in integrations:
        stripe = StripeIngestion(integrations["stripe"])
        snapshots = await stripe.fetch_daily_metrics(db, workspace_id, brand_id)
        for snap in snapshots:
            db.add(snap)
        results["stripe"] = len(snapshots)

    await db.commit()
    return results
