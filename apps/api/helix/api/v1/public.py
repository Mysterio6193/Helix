"""Public stats endpoint — platform metrics for marketing/social proof.

No authentication required. Returns aggregate counts only, no sensitive data.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.db import get_session
from helix.models.brand import Brand
from helix.models.intelligence import IntelligenceSignal
from helix.models.organization import Workspace
from helix.models.workflow import Asset, WorkflowRun

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/stats")
async def get_public_stats(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Return public platform statistics for marketing use."""
    # Count brands
    brands_result = await session.execute(select(func.count()).select_from(Brand))
    total_brands = brands_result.scalar() or 0

    # Count workspaces
    workspaces_result = await session.execute(select(func.count()).select_from(Workspace))
    total_workspaces = workspaces_result.scalar() or 0

    # Count workflow runs
    runs_result = await session.execute(select(func.count()).select_from(WorkflowRun))
    total_runs = runs_result.scalar() or 0

    # Count completed runs
    completed_runs_result = await session.execute(
        select(func.count()).select_from(WorkflowRun).where(WorkflowRun.status == "succeeded")
    )
    completed_runs = completed_runs_result.scalar() or 0

    # Count assets
    assets_result = await session.execute(select(func.count()).select_from(Asset))
    total_assets = assets_result.scalar() or 0

    # Count images
    images_result = await session.execute(
        select(func.count()).select_from(Asset).where(Asset.kind == "image")
    )
    total_images = images_result.scalar() or 0

    # Count videos
    videos_result = await session.execute(
        select(func.count()).select_from(Asset).where(Asset.kind == "video")
    )
    total_videos = videos_result.scalar() or 0

    # Count intelligence signals
    signals_result = await session.execute(select(func.count()).select_from(IntelligenceSignal))
    total_signals = signals_result.scalar() or 0

    # Count active signals (last 24h)
    from datetime import datetime, timedelta
    recent_signals_result = await session.execute(
        select(func.count())
        .select_from(IntelligenceSignal)
        .where(IntelligenceSignal.created_at >= datetime.utcnow() - timedelta(hours=24))
    )
    recent_signals = recent_signals_result.scalar() or 0

    return {
        "brands": total_brands,
        "workspaces": total_workspaces,
        "runs": {
            "total": total_runs,
            "completed": completed_runs,
            "success_rate": round(completed_runs / total_runs * 100, 1) if total_runs > 0 else 0,
        },
        "assets": {
            "total": total_assets,
            "images": total_images,
            "videos": total_videos,
        },
        "intelligence": {
            "total_signals": total_signals,
            "signals_24h": recent_signals,
        },
        "updated_at": datetime.utcnow().isoformat(),
    }
