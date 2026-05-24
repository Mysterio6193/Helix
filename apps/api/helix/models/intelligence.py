"""Intelligence layer models — time-series metrics, segments, competitors, signals."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class PerformanceSnapshot(Base):
    """Raw time-series metrics from connected platforms."""

    __tablename__ = "performance_snapshots"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )

    platform: Mapped[str] = mapped_column(String(32), nullable=False)  # meta_ads, shopify, stripe, klaviyo
    metric_type: Mapped[str] = mapped_column(String(64), nullable=False)  # revenue, roas, ctr, cac, ltv, etc.
    value: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    captured_at: Mapped[datetime] = mapped_column(nullable=False)

    created_at: Mapped[created_at_col]

    __table_args__ = (
        Index("ix_perf_workspace_captured", "workspace_id", "captured_at"),
        Index("ix_perf_platform_metric", "platform", "metric_type"),
        Index("ix_perf_brand_captured", "brand_id", "captured_at"),
    )


class CustomerSegment(Base):
    """Dynamic customer segments computed from order/behavior data."""

    __tablename__ = "customer_segments"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )

    segment_key: Mapped[str] = mapped_column(String(64), nullable=False)  # vip, at_risk, new, loyal, etc.
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    definition_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_ltv: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_order_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    churn_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    retention_curve: Mapped[list[float]] = mapped_column(JSONB, nullable=False, default=list)

    computed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    __table_args__ = (
        Index("ix_segments_workspace_key", "workspace_id", "segment_key", unique=True),
    )


class CompetitorSnapshot(Base):
    """Competitor monitoring snapshots."""

    __tablename__ = "competitor_snapshots"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )

    competitor_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    competitor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snapshot_type: Mapped[str] = mapped_column(String(32), nullable=False)  # pricing, landing_page, ads, social, seo

    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    change_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    diff_from_previous: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    captured_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[created_at_col]

    __table_args__ = (
        Index("ix_competitor_domain_captured", "competitor_domain", "captured_at"),
        Index("ix_competitor_workspace", "workspace_id", "captured_at"),
    )


class IntelligenceSignal(Base):
    """AI-generated insights, anomalies, predictions, and recommendations."""

    __tablename__ = "intelligence_signals"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )

    layer: Mapped[str] = mapped_column(String(32), nullable=False)  # revenue, customer, competitor, campaign, creative
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False)  # anomaly, trend, prediction, opportunity, threat
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="info")  # info, warning, critical

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    auto_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[created_at_col]

    __table_args__ = (
        Index("ix_signals_workspace_layer", "workspace_id", "layer", "created_at"),
        Index("ix_signals_severity", "severity", "created_at"),
    )


class Experiment(Base):
    """A/B and multivariate experiments with statistical rigor."""

    __tablename__ = "experiments"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")  # draft, running, paused, completed, stopped

    # Experiment config
    experiment_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ab")  # ab, multivariate, split_url
    primary_metric: Mapped[str] = mapped_column(String(64), nullable=False, default="conversion_rate")  # conversion_rate, ctr, revenue_per_session
    traffic_allocation: Mapped[int] = mapped_column(Integer, nullable=False, default=100)  # % of traffic in experiment

    # Variants: [{id, name, config, traffic_pct, s3_key?}]
    variants: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    control_variant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # MVT: factors definition: {factor_name: {levels: [{value, config}]}}
    factors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Statistical config
    min_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)  # 0.95 = 95%
    min_sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=100)  # per variant
    auto_stop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Results
    winner: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    uplift: Mapped[float | None] = mapped_column(Float, nullable=True)  # % uplift of winner vs control

    # Computed metrics cache: {variant_id: {impressions, conversions, ctr, revenue}}
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    __table_args__ = (
        Index("ix_experiments_workspace_status", "workspace_id", "status", "created_at"),
        Index("ix_experiments_type", "experiment_type"),
    )


class ExperimentEvent(Base):
    """Individual events tracked for an experiment (impressions, conversions, clicks)."""

    __tablename__ = "experiment_events"

    id: Mapped[uuid_pk]
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )

    variant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)  # impression, conversion, click, revenue
    value: Mapped[float | None] = mapped_column(Float, nullable=True)  # for revenue events

    # Attribution
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)  # meta_ads, shopify, website

    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[created_at_col]

    __table_args__ = (
        Index("ix_exp_events_experiment", "experiment_id", "variant_id", "event_type", "created_at"),
    )
