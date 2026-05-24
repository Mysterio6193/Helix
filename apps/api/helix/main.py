"""FastAPI application entrypoint."""
from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from helix.api.v1 import api_router
from helix.core.config import get_settings
from helix.core.logging import configure_logging, get_logger
from helix.core.metrics import metrics_response
from helix.schemas.common import HealthResponse

settings = get_settings()
configure_logging()
log = get_logger("helix.main")


class HelixException(Exception):
    """Base exception for Helix domain errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info("helix.api.starting", env=settings.helix_env, version=settings.version)

    # Fail-fast safety check: never let dev defaults reach production.
    try:
        settings.assert_production_safe()
    except RuntimeError:
        log.exception("helix.api.unsafe_production_config")
        raise

    # Register all built-in tool adapters
    try:
        from helix.tools.bootstrap import bootstrap_tools

        names = bootstrap_tools(reset=True)
        log.info("helix.api.tools_ready", count=len(names))
    except Exception:
        log.exception("helix.api.tools_bootstrap_failed")

    # Sync skills registry from disk
    try:
        from helix.skills.loader import sync_registry as sync_skills

        skills_synced = await sync_skills()
        log.info("helix.api.skills_ready", count=skills_synced)
    except Exception:
        log.exception("helix.api.skills_sync_failed")

    # Sync design systems library + visual schools
    try:
        from helix.design_systems import sync_design_systems

        ds_synced = await sync_design_systems()
        log.info("helix.api.design_systems_ready", count=ds_synced)
    except Exception:
        log.exception("helix.api.design_systems_sync_failed")

    # Register agents so the API can introspect them
    try:
        from helix.agents.bootstrap import bootstrap_agents

        agent_names = bootstrap_agents()
        log.info("helix.api.agents_ready", count=len(agent_names))
    except Exception:
        log.exception("helix.api.agents_bootstrap_failed")

    # Import slices so workflow registry is populated (used to validate incoming runs)
    try:
        import helix.workflows.slices  # noqa: F401
        from helix.workflows.runner import list_workflows

        log.info("helix.api.workflows_ready", workflows=list_workflows())
    except Exception:
        log.exception("helix.api.workflows_import_failed")

    # Start file watcher if hot_reload is enabled
    if settings.worker_hot_reload:
        try:
            from helix.core.watcher import start_watcher
            await start_watcher()
            log.info("helix.api.watcher_started")
        except Exception:
            log.exception("helix.api.watcher_start_failed")

    yield

    # Cleanup: stop file watcher
    if settings.worker_hot_reload:
        try:
            from helix.core.watcher import stop_watcher
            await stop_watcher()
        except Exception:
            log.exception("helix.api.watcher_stop_failed")

    # Cleanup: close Redis connection
    try:
        from helix.core.redis import close_redis
        await close_redis()
        log.info("helix.api.redis_closed")
    except Exception:
        log.exception("helix.api.redis_close_failed")

    # Cleanup: dispose database engine
    try:
        from helix.core.db import engine
        await engine.dispose()
        log.info("helix.api.db_disposed")
    except Exception:
        log.exception("helix.api.db_dispose_failed")

    log.info("helix.api.stopped")


app = FastAPI(
    title="Helix API",
    description="AI-native creative operating system for restaurants and food brands.",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# CORS: dynamic per-environment. cors_origin_list always returns a concrete
# list (falls back to [web_public_url]) and strips wildcards so credentialed
# requests work in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
    expose_headers=settings.cors_expose_list,
    max_age=settings.cors_max_age,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    """Attach request ID and timing to every request."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())[:8]
    start_time = time.time()

    # Bind request ID to structlog context
    from structlog.contextvars import bind_contextvars
    bind_contextvars(request_id=request_id)

    try:
        response = await call_next(request)
    finally:
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            status_code=getattr(response, "status_code", 0),
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
        )

    response.headers["x-request-id"] = request_id
    response.headers["x-response-time-ms"] = str(round(duration_ms, 2))
    return response


# Global exception handlers
@app.exception_handler(HelixException)
async def helix_exception_handler(request: Request, exc: HelixException) -> JSONResponse:
    log.warning("helix.error", message=exc.message, status=exc.status_code, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": "helix_error"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled.error", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if settings.is_production else str(exc),
            "type": "internal_error",
            "request_id": request.headers.get("x-request-id", "unknown"),
        },
    )


app.include_router(api_router)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    """Deep health check: pings database, Redis, and S3."""
    services: dict[str, str] = {}

    # Database connectivity
    try:
        from helix.core.db import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        services["database"] = "connected"
    except Exception:
        services["database"] = "disconnected"

    # Redis connectivity
    try:
        from helix.core.redis import get_redis
        redis = get_redis()
        await redis.ping()
        services["redis"] = "connected"
    except Exception:
        services["redis"] = "disconnected"

    # S3 connectivity
    try:
        from helix.core.storage import s3_client
        await s3_client.head_bucket(Bucket=settings.s3_bucket)
        services["s3"] = "connected"
    except Exception:
        services["s3"] = "disconnected"

    # Langfuse
    services["langfuse"] = "configured" if settings.langfuse_public_key else "missing"

    # Overall status
    critical = ["database", "redis"]
    status = "ok" if all(services.get(s) == "connected" for s in critical) else "degraded"

    return HealthResponse(
        status=status,
        version=settings.version,
        environment=settings.helix_env,
        services=services,
    )


@app.get("/metrics", tags=["meta"], include_in_schema=False)
async def metrics() -> Response:
    """Prometheus scrape endpoint. Falls back to plain-text counters when the
    `prometheus_client` package is not installed, so /metrics is never broken
    by a missing optional dep."""
    body, content_type = metrics_response()
    return Response(content=body, media_type=content_type)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"name": "helix", "version": settings.version, "docs": "/docs"}
