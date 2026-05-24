"""Public LLM / image gateway endpoints (Higgsfield-style — server holds keys).

All endpoints require authentication. Preferences are scoped to a
workspace owned by the caller's organization (ACL-enforced). Defaults
for tunables come from `settings`, not module-level constants.
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import assert_workspace_access, get_default_workspace_for_user
from helix.core.billing import check_llm_quota
from helix.core.db import get_db, get_session
from helix.core.logging import get_logger
from helix.core.sessions import require_user
from helix.llm.catalog import MODEL_CATALOG, ModelSpec, available_models, default_model, get_model
from helix.llm.gateway import (
    GatewayError,
    complete,
    generate_image,
    generate_video,
    stream_complete,
)
from helix.models.organization import User
from helix.services import user_api_keys as byok_service
from helix.services.usage_tracker import record_usage

router = APIRouter(prefix="/llm", tags=["llm"])
log = get_logger(__name__)


async def _resolve_api_key(
    db: AsyncSession, user: User, provider: str
) -> str | None:
    """Check if the user has a personal API key for this provider (BYOK)."""
    return await byok_service.resolve_plaintext(db, user.id, provider)


PREFS_KEY = "llm_defaults"


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
class ModelEntry(BaseModel):
    id: str
    provider: str
    model: str
    display_name: str
    capability: str
    description: str
    context_window: int | None = None
    max_output_tokens: int | None = None
    input_price_per_1k: float = 0.0
    output_price_per_1k: float = 0.0
    price_per_image: float | None = None
    price_per_second: float | None = None
    tier: str
    is_default: bool = False
    supports_streaming: bool = False
    supports_json_mode: bool = False
    supports_vision: bool = False
    available: bool
    tags: list[str] = Field(default_factory=list)


class CatalogResponse(BaseModel):
    models: list[ModelEntry]
    defaults: dict[str, str | None]


def _spec_to_entry(spec: ModelSpec, available: bool) -> ModelEntry:
    return ModelEntry(
        id=spec.id,
        provider=spec.provider,
        model=spec.model,
        display_name=spec.display_name,
        capability=spec.capability,
        description=spec.description,
        context_window=spec.context_window,
        max_output_tokens=spec.max_output_tokens,
        input_price_per_1k=spec.input_price_per_1k,
        output_price_per_1k=spec.output_price_per_1k,
        price_per_image=spec.price_per_image,
        price_per_second=spec.price_per_second,
        tier=spec.tier,
        is_default=spec.is_default,
        supports_streaming=spec.supports_streaming,
        supports_json_mode=spec.supports_json_mode,
        supports_vision=spec.supports_vision,
        available=available,
        tags=list(spec.tags),
    )


@router.get("/models", response_model=CatalogResponse)
async def list_models(
    capability: Literal["chat", "image", "video", "embedding"] | None = None,
    available_only: bool = False,
    user: User = Depends(require_user),
) -> CatalogResponse:
    avail_ids = {s.id for s in available_models()}
    entries: list[ModelEntry] = []
    for spec in MODEL_CATALOG.values():
        if capability and spec.capability != capability:
            continue
        is_avail = spec.id in avail_ids
        if available_only and not is_avail:
            continue
        entries.append(_spec_to_entry(spec, is_avail))

    defaults: dict[str, str | None] = {}
    for cap in ("chat", "image", "video"):
        d = default_model(cap)  # type: ignore[arg-type]
        defaults[cap] = d.id if d else None

    return CatalogResponse(models=entries, defaults=defaults)


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class CompleteRequest(BaseModel):
    model: str | None = Field(
        default=None,
        description="Catalog model id, e.g. 'openai:gpt-4o-mini'. If omitted, picks the default chat model.",
    )
    prompt: str | None = None
    messages: list[ChatMessage] | None = None
    system: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1500, ge=1, le=32000)
    json_mode: bool = False


class CompleteResponse(BaseModel):
    text: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None


# ---------------------------------------------------------------------------
# Playground — compare multiple models side by side
# ---------------------------------------------------------------------------
class PlaygroundRequest(BaseModel):
    models: list[str] = Field(
        min_length=2, max_length=6,
        description="Model IDs to compare (2-6 models).",
    )
    prompt: str | None = None
    messages: list[ChatMessage] | None = None
    system: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1500, ge=1, le=32000)


class PlaygroundResult(BaseModel):
    model: str
    provider: str
    display_name: str | None = None
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float | None = None
    error: str | None = None


class PlaygroundResponse(BaseModel):
    results: list[PlaygroundResult]


@router.post("/playground")
async def playground_endpoint(
    payload: PlaygroundRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> PlaygroundResponse:
    if not payload.prompt and not payload.messages:
        raise HTTPException(status_code=400, detail="prompt or messages required")

    quota = await check_llm_quota(db, user.organization_id)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly LLM call limit reached ({quota['used']}/{quota['limit']}). Upgrade your plan to continue.",
        )

    from helix.core.db import AsyncSessionLocal
    from helix.llm.catalog import get_model as resolve_model

    async def run_one(model_id: str) -> PlaygroundResult:
        spec = resolve_model(model_id)
        async with AsyncSessionLocal() as task_db:
            api_key = await _resolve_api_key(task_db, user, spec.provider) if spec else None
            start = time.monotonic()
            try:
                result = await complete(
                    model=model_id,
                    prompt=payload.prompt,
                    messages=[m.model_dump() for m in payload.messages] if payload.messages else None,
                    system=payload.system,
                    temperature=payload.temperature,
                    max_tokens=payload.max_tokens,
                    api_key=api_key,
                )
                elapsed = (time.monotonic() - start) * 1000
                try:
                    await record_usage(
                        db=task_db,
                        user_id=user.id,
                        organization_id=user.organization_id,
                        model_id=result.model,
                        provider=result.provider,
                        prompt_tokens=result.prompt_tokens or 0,
                        completion_tokens=result.completion_tokens or 0,
                        cost_usd=result.cost_usd,
                    )
                except Exception:
                    log.warning("playground.usage_track_failed", model=model_id)
                return PlaygroundResult(
                    model=result.model,
                    provider=result.provider,
                    display_name=spec.display_name if spec else None,
                    text=result.text,
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    cost_usd=result.cost_usd,
                    latency_ms=round(elapsed, 1),
                )
            except GatewayError as exc:
                elapsed = (time.monotonic() - start) * 1000
                return PlaygroundResult(
                    model=model_id,
                    provider=spec.provider if spec else "unknown",
                    error=str(exc),
                    text="",
                    latency_ms=round(elapsed, 1),
                )

    tasks = [run_one(mid) for mid in payload.models]
    results_list = await asyncio.gather(*tasks)
    return PlaygroundResponse(results=list(results_list))


@router.post("/complete", response_model=CompleteResponse)
async def complete_endpoint(
    payload: CompleteRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> CompleteResponse:
    if not payload.prompt and not payload.messages:
        raise HTTPException(status_code=400, detail="prompt or messages required")

    # Plan quota check
    quota = await check_llm_quota(db, user.organization_id)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly LLM call limit reached ({quota['used']}/{quota['limit']}). Upgrade your plan to continue.",
        )

    # Resolve the model spec first so we know the provider for BYOK lookup
    from helix.llm.catalog import get_model as resolve_model
    spec = resolve_model(payload.model) if payload.model else None

    api_key = None
    if spec:
        api_key = await _resolve_api_key(db, user, spec.provider)

    try:
        result = await complete(
            model=payload.model,
            prompt=payload.prompt,
            messages=[m.model_dump() for m in payload.messages] if payload.messages else None,
            system=payload.system,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            json_mode=payload.json_mode,
            api_key=api_key,
        )
    except GatewayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log.info("llm.complete", model=result.model, cost_usd=result.cost_usd, user_id=str(user.id))

    # Track usage for subscription billing
    try:
        await record_usage(
            db=db,
            user_id=user.id,
            organization_id=user.organization_id,
            model_id=result.model,
            provider=result.provider,
            prompt_tokens=result.prompt_tokens or 0,
            completion_tokens=result.completion_tokens or 0,
            cost_usd=result.cost_usd,
        )
    except Exception:
        log.warning("llm.usage_track_failed", user_id=str(user.id))

    return CompleteResponse(**result.to_dict())


# ---------------------------------------------------------------------------
# Streaming (SSE)
# ---------------------------------------------------------------------------
@router.post("/stream")
async def stream_endpoint(
    payload: CompleteRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    if not payload.prompt and not payload.messages:
        raise HTTPException(status_code=400, detail="prompt or messages required")

    # Plan quota check
    quota = await check_llm_quota(db, user.organization_id)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly LLM call limit reached ({quota['used']}/{quota['limit']}). Upgrade your plan to continue.",
        )

    from helix.llm.catalog import get_model as resolve_model
    spec = resolve_model(payload.model) if payload.model else None
    api_key = None
    if spec:
        api_key = await _resolve_api_key(db, user, spec.provider)

    async def gen():
        try:
            async for chunk in stream_complete(
                model=payload.model,
                prompt=payload.prompt,
                messages=[m.model_dump() for m in payload.messages] if payload.messages else None,
                system=payload.system,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
                api_key=api_key,
            ):
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except GatewayError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
class ImageRequest(BaseModel):
    model: str | None = None
    prompt: str
    size: str = "1024x1024"
    quality: str = "high"
    n: int = Field(default=1, ge=1, le=10)


class ImageItem(BaseModel):
    s3_key: str
    width: int
    height: int
    source_url: str | None = None


class ImageResponse(BaseModel):
    images: list[ImageItem]
    model: str
    provider: str
    cost_usd: float | None = None


@router.post("/images", response_model=ImageResponse)
async def images_endpoint(
    payload: ImageRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ImageResponse:
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt required")

    quota = await check_llm_quota(db, user.organization_id)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly call limit reached ({quota['used']}/{quota['limit']}). Upgrade your plan to continue.",
        )

    try:
        result = await generate_image(
            model=payload.model,
            prompt=payload.prompt,
            size=payload.size,
            quality=payload.quality,
            n=payload.n,
        )
    except GatewayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log.info(
        "llm.images",
        model=result.model,
        count=len(result.images),
        cost_usd=result.cost_usd,
        user_id=str(user.id),
    )
    return ImageResponse(
        images=[ImageItem(**img) for img in result.images],
        model=result.model,
        provider=result.provider,
        cost_usd=result.cost_usd,
    )


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------
class VideoRequest(BaseModel):
    model: str | None = None
    prompt: str
    duration_seconds: int = Field(default=5, ge=3, le=10)
    aspect_ratio: str = "16:9"


class VideoItem(BaseModel):
    s3_key: str
    duration_seconds: int
    source_url: str | None = None


class VideoResponse(BaseModel):
    videos: list[VideoItem]
    model: str
    provider: str
    cost_usd: float | None = None


@router.post("/videos", response_model=VideoResponse)
async def videos_endpoint(
    payload: VideoRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt required")

    quota = await check_llm_quota(db, user.organization_id)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly call limit reached ({quota['used']}/{quota['limit']}). Upgrade your plan to continue.",
        )
    try:
        result = await generate_video(
            model=payload.model,
            prompt=payload.prompt,
            duration_seconds=payload.duration_seconds,
            aspect_ratio=payload.aspect_ratio,
        )
    except GatewayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log.info(
        "llm.videos",
        model=result.model,
        count=len(result.videos),
        cost_usd=result.cost_usd,
        user_id=str(user.id),
    )
    return VideoResponse(
        videos=[VideoItem(**v) for v in result.videos],
        model=result.model,
        provider=result.provider,
        cost_usd=result.cost_usd,
    )


# ---------------------------------------------------------------------------
# Workspace defaults — ACL-scoped to caller's organization.
# ---------------------------------------------------------------------------
class WorkspacePrefs(BaseModel):
    workspace_id: str
    default_chat_model: str | None = None
    default_image_model: str | None = None
    default_video_model: str | None = None


class PrefsUpdate(BaseModel):
    default_chat_model: str | None = None
    default_image_model: str | None = None
    default_video_model: str | None = None


def _validate_model(model_id: str | None, expected_cap: str) -> None:
    if model_id is None:
        return
    spec = get_model(model_id)
    if spec is None:
        raise HTTPException(status_code=400, detail=f"unknown model: {model_id}")
    if spec.capability != expected_cap:
        raise HTTPException(
            status_code=400,
            detail=f"model {model_id} is a {spec.capability} model, not {expected_cap}",
        )


async def _resolve_workspace(
    session: AsyncSession,
    user: User,
    workspace_id: uuid.UUID | None,
):
    if workspace_id is not None:
        return await assert_workspace_access(session, user, workspace_id)
    return await get_default_workspace_for_user(session, user)


@router.get("/preferences", response_model=WorkspacePrefs)
async def get_preferences(
    workspace_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> WorkspacePrefs:
    workspace = await _resolve_workspace(session, user, workspace_id)
    prefs = (workspace.settings or {}).get(PREFS_KEY) or {}

    chat_default = default_model("chat")
    image_default = default_model("image")
    video_default = default_model("video")

    return WorkspacePrefs(
        workspace_id=str(workspace.id),
        default_chat_model=prefs.get("chat") or (chat_default.id if chat_default else None),
        default_image_model=prefs.get("image") or (image_default.id if image_default else None),
        default_video_model=prefs.get("video") or (video_default.id if video_default else None),
    )


@router.put("/preferences", response_model=WorkspacePrefs)
async def update_preferences(
    payload: PrefsUpdate,
    workspace_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> WorkspacePrefs:
    _validate_model(payload.default_chat_model, "chat")
    _validate_model(payload.default_image_model, "image")
    _validate_model(payload.default_video_model, "video")

    workspace = await _resolve_workspace(session, user, workspace_id)
    settings_obj = dict(workspace.settings or {})
    prefs = dict(settings_obj.get(PREFS_KEY) or {})
    if payload.default_chat_model is not None:
        prefs["chat"] = payload.default_chat_model
    if payload.default_image_model is not None:
        prefs["image"] = payload.default_image_model
    if payload.default_video_model is not None:
        prefs["video"] = payload.default_video_model
    settings_obj[PREFS_KEY] = prefs
    workspace.settings = settings_obj
    await session.flush()
    await session.commit()

    chat_default = default_model("chat")
    image_default = default_model("image")
    video_default = default_model("video")

    return WorkspacePrefs(
        workspace_id=str(workspace.id),
        default_chat_model=prefs.get("chat") or (chat_default.id if chat_default else None),
        default_image_model=prefs.get("image") or (image_default.id if image_default else None),
        default_video_model=prefs.get("video") or (video_default.id if video_default else None),
    )
