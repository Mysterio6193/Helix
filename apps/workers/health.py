"""Worker health check server for K8s liveness/readiness probes.

Exposes GET /healthz with worker state: in-flight count, processed total,
DLQ depth, and readiness flag.  Runs as a background asyncio task alongside
the main BLPOP consumer loop.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from aiohttp import web

from helix.core.config import get_settings
from helix.core.logging import get_logger

log = get_logger("helix.worker.health")


@dataclass
class WorkerState:
    """Shared counters between the worker loop and health server."""

    semaphore: asyncio.Semaphore | None = None
    concurrency: int = 8
    processed: int = 0
    failed: int = 0
    dlq_depth: int = 0
    ready: bool = False
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def in_flight(self) -> int:
        if self.semaphore is None:
            return 0
        return self.concurrency - self.semaphore._value  # noqa: SLF001

    async def inc_processed(self) -> None:
        async with self._lock:
            self.processed += 1

    async def inc_failed(self) -> None:
        async with self._lock:
            self.failed += 1

    async def inc_dlq(self) -> None:
        async with self._lock:
            self.dlq_depth += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "in_flight": self.in_flight,
            "processed": self.processed,
            "failed": self.failed,
            "dlq_depth": self.dlq_depth,
            "concurrency": self.concurrency,
        }


async def _healthz(request: web.Request) -> web.Response:
    state: WorkerState = request.app["worker_state"]
    return web.json_response(state.snapshot())


async def start_health_server(state: WorkerState) -> web.AppRunner:
    """Start the health server as a background aiohttp app.

    Returns the runner so callers can clean up on shutdown.
    """
    settings = get_settings()
    port = settings.worker_healthz_port

    app = web.Application()
    app["worker_state"] = state
    app.router.add_get("/healthz", _healthz)

    runner = web.AppRunner(app, handle_signals=False)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("worker.health_started", port=port)
    return runner
