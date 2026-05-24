"""Media generation API — batch image/video generation jobs."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import list_user_workspace_ids
from helix.core.db import get_session
from helix.core.logging import get_logger
from helix.core.sessions import require_user
from helix.llm import generate_image, generate_video
from helix.models.generation import MediaGenerationJob
from helix.models.organization import User
from helix.models.workflow import Asset

router = APIRouter(prefix="/media", tags=["media"])
log = get_logger(__name__)


# ─── Schemas ──────────────────────────────────────────────────────────

class MediaGenerateRequest(BaseModel):
    name: str
    job_type: str = Field(..., pattern="^(image|video|batch)$")
    model: str | None = None
    prompts: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class MediaJobResponse(BaseModel):
    id: str
    name: str
    job_type: str
    status: str
    model: str | None
    total_items: int
    completed_items: int
    failed_items: int
    total_cost_usd: float | None
    created_at: str | None
    started_at: str | None
    completed_at: str | None


class MediaJobDetailResponse(MediaJobResponse):
    prompts: list[str]
    results: list[dict[str, Any]]
    error: str | None


# ─── Jobs ─────────────────────────────────────────────────────────────

@router.get("/jobs", response_model=list[MediaJobResponse])
async def list_jobs(
    status: str | None = None,
    job_type: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> list[MediaJobResponse]:
    """Return media generation jobs."""
    workspace_ids = await list_user_workspace_ids(session, user)

    query = select(MediaGenerationJob).where(MediaGenerationJob.workspace_id.in_(workspace_ids))
    if status:
        query = query.where(MediaGenerationJob.status == status)
    if job_type:
        query = query.where(MediaGenerationJob.job_type == job_type)

    query = query.order_by(desc(MediaGenerationJob.created_at)).limit(limit)
    result = await session.execute(query)

    return [
        MediaJobResponse(
            id=str(j.id),
            name=j.name,
            job_type=j.job_type,
            status=j.status,
            model=j.model,
            total_items=j.total_items,
            completed_items=j.completed_items,
            failed_items=j.failed_items,
            total_cost_usd=j.total_cost_usd,
            created_at=j.created_at.isoformat() if j.created_at else None,
            started_at=j.started_at.isoformat() if j.started_at else None,
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
        )
        for j in result.scalars().all()
    ]


@router.post("/jobs", response_model=MediaJobResponse)
async def create_job(
    payload: MediaGenerateRequest,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> MediaJobResponse:
    """Create a media generation job."""
    workspace_ids = await list_user_workspace_ids(session, user)
    if not workspace_ids:
        raise HTTPException(status_code=400, detail="No workspace available")

    job = MediaGenerationJob(
        workspace_id=workspace_ids[0],
        created_by=user.id,
        name=payload.name,
        job_type=payload.job_type,
        model=payload.model,
        prompts=payload.prompts,
        config=payload.config,
        total_items=len(payload.prompts),
        status="pending",
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    log.info("media_job_created", job=str(job.id), type=payload.job_type, items=len(payload.prompts))

    return MediaJobResponse(
        id=str(job.id),
        name=job.name,
        job_type=job.job_type,
        status=job.status,
        model=job.model,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        total_cost_usd=job.total_cost_usd,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=None,
        completed_at=None,
    )


@router.get("/jobs/{job_id}", response_model=MediaJobDetailResponse)
async def get_job(
    job_id: UUID,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> MediaJobDetailResponse:
    """Get job details with results."""
    result = await session.execute(
        select(MediaGenerationJob).where(MediaGenerationJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return MediaJobDetailResponse(
        id=str(job.id),
        name=job.name,
        job_type=job.job_type,
        status=job.status,
        model=job.model,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        total_cost_usd=job.total_cost_usd,
        prompts=job.prompts,
        results=job.results,
        error=job.error,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.post("/jobs/{job_id}/run", response_model=MediaJobDetailResponse)
async def run_job(
    job_id: UUID,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> MediaJobDetailResponse:
    """Execute a pending media generation job."""
    result = await session.execute(
        select(MediaGenerationJob).where(MediaGenerationJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("pending", "failed"):
        raise HTTPException(status_code=400, detail=f"Job status is {job.status}, cannot run")

    job.status = "running"
    job.started_at = datetime.utcnow()
    job.completed_items = 0
    job.failed_items = 0
    job.results = []
    job.total_cost_usd = 0.0
    job.error = None
    await session.commit()

    log.info("media_job_started", job=str(job.id), type=job.job_type, items=job.total_items)

    results = []
    total_cost = 0.0

    try:
        for i, prompt in enumerate(job.prompts):
            try:
                if job.job_type == "image":
                    gen_result = await generate_image(
                        model=job.model,
                        prompt=prompt,
                        size=job.config.get("size", "1024x1024"),
                        quality=job.config.get("quality", "high"),
                        n=1,
                        s3_prefix="generated/media",
                    )
                    for img in gen_result.images:
                        results.append({
                            "type": "image",
                            "prompt": prompt,
                            "s3_key": img["s3_key"],
                            "width": img.get("width"),
                            "height": img.get("height"),
                            "cost_usd": gen_result.cost_usd,
                        })
                        # Create Asset record
                        asset = Asset(
                            workspace_id=job.workspace_id,
                            brand_id=job.brand_id,
                            kind="image",
                            mime_type="image/png",
                            s3_key=img["s3_key"],
                            width=img.get("width"),
                            height=img.get("height"),
                            metadata_={
                                "generated_by": "media_job",
                                "job_id": str(job.id),
                                "prompt": prompt,
                                "model": gen_result.model,
                            },
                        )
                        session.add(asset)
                    total_cost += gen_result.cost_usd or 0.0

                elif job.job_type == "video":
                    gen_result = await generate_video(
                        model=job.model,
                        prompt=prompt,
                        duration_seconds=job.config.get("duration_seconds", 5),
                        s3_prefix="generated/media",
                        aspect_ratio=job.config.get("aspect_ratio", "16:9"),
                    )
                    for vid in gen_result.videos:
                        results.append({
                            "type": "video",
                            "prompt": prompt,
                            "s3_key": vid["s3_key"],
                            "duration_seconds": vid.get("duration_seconds"),
                            "cost_usd": gen_result.cost_usd,
                        })
                        asset = Asset(
                            workspace_id=job.workspace_id,
                            brand_id=job.brand_id,
                            kind="video",
                            mime_type="video/mp4",
                            s3_key=vid["s3_key"],
                            metadata_={
                                "generated_by": "media_job",
                                "job_id": str(job.id),
                                "prompt": prompt,
                                "model": gen_result.model,
                                "duration_seconds": vid.get("duration_seconds"),
                            },
                        )
                        session.add(asset)
                    total_cost += gen_result.cost_usd or 0.0

                job.completed_items = i + 1
                await session.commit()

            except Exception as e:
                log.error("media_job_item_failed", job=str(job.id), item=i, error=str(e))
                results.append({
                    "type": job.job_type,
                    "prompt": prompt,
                    "error": str(e),
                    "status": "failed",
                })
                job.failed_items += 1
                await session.commit()

        job.status = "completed" if job.failed_items == 0 else "failed"
        job.completed_at = datetime.utcnow()
        job.results = results
        job.total_cost_usd = total_cost

        log.info("media_job_completed",
                job=str(job.id),
                completed=job.completed_items,
                failed=job.failed_items,
                cost=total_cost)

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        log.error("media_job_failed", job=str(job.id), error=str(e))

    await session.commit()

    return MediaJobDetailResponse(
        id=str(job.id),
        name=job.name,
        job_type=job.job_type,
        status=job.status,
        model=job.model,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        total_cost_usd=job.total_cost_usd,
        prompts=job.prompts,
        results=job.results,
        error=job.error,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Cancel a pending or running job."""
    result = await session.execute(
        select(MediaGenerationJob).where(MediaGenerationJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"Job status is {job.status}, cannot cancel")

    job.status = "cancelled"
    job.cancelled_at = datetime.utcnow()
    await session.commit()

    return {"id": str(job_id), "status": "cancelled"}


# ─── Templates ────────────────────────────────────────────────────────

@router.get("/templates")
async def list_templates() -> list[dict[str, Any]]:
    """Return available media generation templates."""
    return [
        {
            "id": "ad_creative",
            "name": "Ad Creative Variant",
            "type": "image",
            "prompt_template": "Professional product photography of {product} on a clean {background} background, {style} lighting, high-end commercial aesthetic, 8k quality",
            "description": "Generate ad-ready product photography",
        },
        {
            "id": "social_feed",
            "name": "Social Feed Post",
            "type": "image",
            "prompt_template": "Eye-catching social media graphic for {brand}, {theme} theme, bold typography space, vibrant colors, Instagram feed optimized, 1:1 square",
            "description": "Generate Instagram feed graphics",
        },
        {
            "id": "social_story",
            "name": "Instagram Story",
            "type": "image",
            "prompt_template": "Vertical Instagram story design for {brand}, {theme} style, swipe-up CTA space at bottom, 9:16 aspect ratio, modern minimal",
            "description": "Generate Instagram story templates",
        },
        {
            "id": "product_video",
            "name": "Product Showcase Video",
            "type": "video",
            "prompt_template": "Cinematic product showcase of {product}, smooth camera movement, studio lighting, professional commercial, 5 seconds",
            "description": "Generate short product videos",
        },
        {
            "id": "brand_hero",
            "name": "Brand Hero Image",
            "type": "image",
            "prompt_template": "Stunning hero image for {brand} website, {theme} aesthetic, wide banner composition, premium feel, 16:9 aspect ratio",
            "description": "Generate website hero banners",
        },
        {
            "id": "creative_fatigue_refresh",
            "name": "Creative Fatigue Refresh",
            "type": "batch",
            "prompt_template": "{style} ad creative for {product}, version {variant}, unique angle and composition, commercial photography",
            "description": "Generate 3 variant images for creative refresh",
        },
    ]
