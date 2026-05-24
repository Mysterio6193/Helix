"""Power API — Exposes advanced capabilities: swarm, multimodal, analytics, jobs, webhooks."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from helix.agents.swarm import get_swarm
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.multimodal import audio, ocr, vision
from helix.services.advanced_analytics import (
    attribution_model,
    causal_analyzer,
    churn_predictor,
    clv_predictor,
    revenue_forecaster,
)
from helix.services.jobs import JobPriority, enqueue_job, get_job_queue
from helix.services.prompt_optimizer import get_prompt_optimizer
from helix.services.webhooks import WebhookEndpoint, get_webhook_manager

router = APIRouter(prefix="/power", tags=["power"])


# ─── Agent Swarm ─────────────────────────────────────────────────────────

class SwarmRequest(BaseModel):
    goal: str
    context: dict[str, Any] = Field(default_factory=dict)


class BrainstormRequest(BaseModel):
    topic: str
    num_agents: int = Field(default=5, ge=2, le=10)
    rounds: int = Field(default=3, ge=1, le=5)


@router.post("/swarm/execute")
async def swarm_execute(payload: SwarmRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    swarm = get_swarm()
    return await swarm.execute(payload.goal, payload.context)


@router.post("/swarm/brainstorm")
async def swarm_brainstorm(payload: BrainstormRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    swarm = get_swarm()
    return await swarm.brainstorm(payload.topic, payload.num_agents, payload.rounds)


# ─── Multi-modal AI ──────────────────────────────────────────────────────

class VisionRequest(BaseModel):
    image_url: str | None = None
    image_base64: str | None = None
    prompt: str = "Describe this image in detail."


@router.post("/vision/analyze")
async def vision_analyze(payload: VisionRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    return await vision.analyze_image(
        image_url=payload.image_url,
        image_base64=payload.image_base64,
        prompt=payload.prompt,
    )


class OCRRequest(BaseModel):
    image_url: str | None = None
    image_base64: str | None = None
    document_type: str = "general"


@router.post("/ocr/extract")
async def ocr_extract(payload: OCRRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    return await ocr.extract_text(
        image_url=payload.image_url,
        image_base64=payload.image_base64,
        document_type=payload.document_type,
    )


class TranscribeRequest(BaseModel):
    audio_url: str | None = None
    language: str | None = None


@router.post("/audio/transcribe")
async def audio_transcribe(payload: TranscribeRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    return await audio.transcribe(audio_url=payload.audio_url, language=payload.language)


# ─── Advanced Analytics ─────────────────────────────────────────────────

@router.post("/analytics/clv")
async def predict_clv(customer: dict[str, Any], user: User = Depends(require_user)) -> dict[str, Any]:
    return clv_predictor.predict(customer)


@router.post("/analytics/causal")
async def causal_analysis(
    pre_period: list[dict[str, Any]],
    post_period: list[dict[str, Any]],
    metric: str = "revenue",
    user: User = Depends(require_user),
) -> dict[str, Any]:
    return causal_analyzer.analyze(pre_period, post_period, metric)


@router.post("/analytics/attribution")
async def attribution_analysis(
    touchpoints: list[dict[str, Any]],
    conversion_value: float,
    model: str = "linear",
    user: User = Depends(require_user),
) -> dict[str, Any]:
    if model == "linear":
        return attribution_model.linear_attribution(touchpoints, conversion_value)
    elif model == "time_decay":
        return attribution_model.time_decay_attribution(touchpoints, conversion_value)
    elif model == "first_touch":
        return attribution_model.first_touch_attribution(touchpoints, conversion_value)
    elif model == "compare":
        return attribution_model.compare_models(touchpoints, conversion_value)
    raise HTTPException(status_code=400, detail=f"Unknown attribution model: {model}")


@router.post("/analytics/churn")
async def churn_prediction(customer: dict[str, Any], user: User = Depends(require_user)) -> dict[str, Any]:
    return churn_predictor.predict(customer)


@router.post("/analytics/forecast")
async def revenue_forecast(
    historical: list[dict[str, Any]],
    days_ahead: int = 30,
    user: User = Depends(require_user),
) -> dict[str, Any]:
    return revenue_forecaster.forecast(historical, days_ahead)


# ─── Background Jobs ────────────────────────────────────────────────────

class EnqueueJobRequest(BaseModel):
    name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = JobPriority.NORMAL.value
    tags: list[str] = Field(default_factory=list)


@router.post("/jobs/enqueue")
async def enqueue_job_endpoint(payload: EnqueueJobRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    job = await enqueue_job(payload.name, payload.payload, payload.priority, tags=payload.tags)
    return job.to_dict()


@router.get("/jobs/stats")
async def job_stats(user: User = Depends(require_user)) -> dict[str, Any]:
    queue = get_job_queue()
    return await queue.get_stats()


@router.get("/jobs/list")
async def list_jobs(
    status: str | None = None,
    limit: int = 50,
    user: User = Depends(require_user),
) -> list[dict[str, Any]]:
    queue = get_job_queue()
    jobs = await queue.list_jobs(status=status, limit=limit)
    return [j.to_dict() for j in jobs]


# ─── Webhooks ───────────────────────────────────────────────────────────

class WebhookRegisterRequest(BaseModel):
    url: str
    secret: str
    events: list[str] = Field(default_factory=list)
    headers: dict[str, str] | None = None


@router.post("/webhooks/register")
async def register_webhook(payload: WebhookRegisterRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    manager = get_webhook_manager()
    endpoint = WebhookEndpoint(
        id=f"wh_{user.id}_{int(time.time())}",
        url=payload.url,
        secret=payload.secret,
        events=payload.events,
        headers=payload.headers,
    )
    await manager.register(endpoint)
    return {"success": True, "endpoint_id": endpoint.id}


@router.get("/webhooks/list")
async def list_webhooks(user: User = Depends(require_user)) -> list[dict[str, Any]]:
    manager = get_webhook_manager()
    endpoints = await manager.list_endpoints()
    return [
        {
            "id": ep.id,
            "url": ep.url,
            "events": ep.events,
            "active": ep.active,
            "created_at": ep.created_at,
        }
        for ep in endpoints
    ]


@router.delete("/webhooks/{endpoint_id}")
async def delete_webhook(endpoint_id: str, user: User = Depends(require_user)) -> dict[str, Any]:
    manager = get_webhook_manager()
    success = await manager.unregister(endpoint_id)
    return {"success": success}


@router.post("/webhooks/trigger")
async def trigger_webhook(
    event_type: str,
    payload: dict[str, Any],
    user: User = Depends(require_user),
) -> list[dict[str, Any]]:
    manager = get_webhook_manager()
    return await manager.trigger_event(event_type, payload)


# ─── Prompt Optimization ────────────────────────────────────────────────

class OptimizePromptRequest(BaseModel):
    prompt: str
    test_cases: list[dict[str, Any]] = Field(default_factory=list)
    num_variants: int = Field(default=3, ge=1, le=5)


@router.post("/prompts/optimize")
async def optimize_prompt(payload: OptimizePromptRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    from helix.services.prompt_optimizer import PromptTest

    optimizer = get_prompt_optimizer()
    tests = [PromptTest(**tc) for tc in payload.test_cases]
    return await optimizer.optimize(payload.prompt, tests, payload.num_variants)


# ─── Cache Management ───────────────────────────────────────────────────

@router.get("/cache/stats")
async def cache_stats(user: User = Depends(require_user)) -> dict[str, Any]:
    from helix.core.cache import get_cache
    cache = get_cache()
    return cache.stats


@router.post("/cache/invalidate")
async def invalidate_cache(namespace: str, user: User = Depends(require_user)) -> dict[str, Any]:
    from helix.core.cache import get_cache
    cache = get_cache()
    await cache.invalidate_namespace(namespace)
    return {"success": True, "namespace": namespace}
