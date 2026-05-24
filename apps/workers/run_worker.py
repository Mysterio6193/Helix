"""Helix worker — consumes workflow run jobs from Redis and executes them.

Jobs are pushed onto the `helix:runs` list by the API when a WorkflowRun is created.
Each job is JSON: {"run_id": "...", "brand_id": "...", "workspace_id": "...",
"workflow": "...", "inputs": {...}, "config": {...}}.

Concurrency is controlled by an asyncio.Semaphore sized to
`settings.worker_concurrency` (default 8).  Failed jobs are retried with
exponential backoff via a Redis sorted set (`helix:runs:delayed`).  Jobs that
exhaust retries are moved to a dead-letter queue (`helix:runs:dlq`).
"""
from __future__ import annotations

import asyncio
import json
import signal
import time
from typing import TYPE_CHECKING
from uuid import UUID

import redis.asyncio as aioredis

if TYPE_CHECKING:
    from helix.workers.health import WorkerState

from helix.agents.bootstrap import bootstrap_agents
from helix.core.config import get_settings
from helix.core.logging import configure_logging, get_logger
from helix.design_systems import sync_design_systems
from helix.skills.loader import sync_registry as sync_skills
from helix.tools.bootstrap import bootstrap_tools
from helix.workers.sweeper import run_sweeper
from helix.workflows.runner import execute_run
from helix.workflows.state import RunContext

# Queue key + derivatives are driven by settings.run_queue_key so a single
# env var rebrands every list, sorted set, and DLQ used by the worker pool.
_settings = get_settings()
QUEUE_KEY = _settings.run_queue_key
DELAYED_KEY = f"{QUEUE_KEY}:delayed"
DLQ_KEY = f"{QUEUE_KEY}:dlq"
POP_TIMEOUT = 5  # seconds — short BLPOP so shutdown is responsive


configure_logging()
log = get_logger("helix.worker")


_shutdown = asyncio.Event()


def _install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    def _stop(_signum: int, _frame: object | None = None) -> None:
        log.info("worker.shutdown_signal")
        loop.call_soon_threadsafe(_shutdown.set)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop, sig, None)
        except NotImplementedError:  # pragma: no cover — non-unix
            signal.signal(sig, _stop)


# ---------------------------------------------------------------------------
# Job processing
# ---------------------------------------------------------------------------

async def _process(
    job: dict,
    client: aioredis.Redis,
    worker_state: "WorkerState",
) -> None:
    """Process a single job.  On failure, retry or send to DLQ."""
    settings = get_settings()
    retries = job.get("retries", 0)

    try:
        ctx = RunContext(
            run_id=UUID(job["run_id"]),
            brand_id=UUID(job["brand_id"]),
            workspace_id=UUID(job["workspace_id"]),
            workflow=job["workflow"],
            inputs=job.get("inputs", {}),
            config=job.get("config", {}),
            user_id=UUID(job["user_id"]) if job.get("user_id") else None,
        )
    except Exception:
        log.exception("worker.invalid_job", job=job)
        await client.lpush(DLQ_KEY, json.dumps(job))  # type: ignore[misc]
        await worker_state.inc_dlq()
        return

    log.info(
        "worker.run_start",
        run_id=str(ctx.run_id),
        workflow=ctx.workflow,
        attempt=retries + 1,
    )
    try:
        await execute_run(ctx)
        log.info("worker.run_done", run_id=str(ctx.run_id))
        await worker_state.inc_processed()
    except Exception:
        log.exception(
            "worker.run_failed",
            run_id=str(ctx.run_id),
            attempt=retries + 1,
        )
        await worker_state.inc_failed()

        if retries < settings.worker_max_retries:
            # Exponential backoff: base^retries seconds
            delay = settings.worker_retry_base_seconds ** (retries + 1)
            job["retries"] = retries + 1
            score = time.time() + delay
            await client.zadd(DELAYED_KEY, {json.dumps(job): score})
            log.info(
                "worker.retry_scheduled",
                run_id=str(ctx.run_id),
                retry=retries + 1,
                delay_s=delay,
            )
        else:
            await client.lpush(DLQ_KEY, json.dumps(job))  # type: ignore[misc]
            await worker_state.inc_dlq()
            log.warning(
                "worker.dlq",
                run_id=str(ctx.run_id),
                retries=retries,
            )


async def _process_with_semaphore(
    job: dict,
    sem: asyncio.Semaphore,
    client: aioredis.Redis,
    worker_state: "WorkerState",
) -> None:
    """Acquire semaphore then process.  Ensures bounded concurrency."""
    async with sem:
        await _process(job, client, worker_state)


# ---------------------------------------------------------------------------
# Delayed queue drain — re-queue mature delayed jobs
# ---------------------------------------------------------------------------

async def _drain_delayed(client: aioredis.Redis) -> None:
    """Continuously move mature delayed jobs back to the main queue."""
    while not _shutdown.is_set():
        try:
            now = time.time()
            # Fetch delayed jobs whose score <= now (ready to retry)
            mature = await client.zrangebyscore(DELAYED_KEY, 0, now, start=0, num=50)
            if mature:
                pipe = client.pipeline()
                for raw in mature:
                    pipe.rpush(QUEUE_KEY, raw)
                pipe.zremrangebyscore(DELAYED_KEY, 0, now)
                await pipe.execute()
                log.info("worker.delayed_drained", count=len(mature))
        except Exception:
            log.exception("worker.delayed_drain_error")
        await asyncio.sleep(1)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def main() -> None:
    settings = get_settings()
    loop = asyncio.get_running_loop()
    _install_signal_handlers(loop)

    # Bootstrap registries (tools, agents, skills, design systems)
    bootstrap_tools(reset=True)
    bootstrap_agents()
    
    from helix.workflows.checkpointer import setup_checkpointer, close_checkpointer
    try:
        await setup_checkpointer()
    except Exception:
        log.exception("worker.checkpointer_setup_failed")

    try:
        await sync_skills()
    except Exception:
        log.exception("worker.skills_sync_failed")
    try:
        await sync_design_systems()
    except Exception:
        log.exception("worker.design_systems_sync_failed")

    # Start file watcher if hot_reload is enabled
    if settings.worker_hot_reload:
        try:
            from helix.core.watcher import start_watcher
            await start_watcher()
            log.info("worker.watcher_started")
        except Exception:
            log.exception("worker.watcher_start_failed")

    # Lazy-import slice registrations so they self-register into _WORKFLOWS
    try:
        import helix.workflows.slices  # noqa: F401
    except Exception:
        log.exception("worker.slices_import_failed")

    # -- Concurrency semaphore --
    sem = asyncio.Semaphore(settings.worker_concurrency)

    # -- Worker state for health checks --
    from helix.workers.health import WorkerState, start_health_server

    worker_state = WorkerState(
        semaphore=sem,
        concurrency=settings.worker_concurrency,
    )

    # Start health server
    health_runner = await start_health_server(worker_state)

    # -- Redis client --
    client = aioredis.from_url(settings.redis_url, decode_responses=True)

    worker_state.ready = True
    log.info(
        "worker.ready",
        queue=QUEUE_KEY,
        redis=settings.redis_url,
        concurrency=settings.worker_concurrency,
        max_retries=settings.worker_max_retries,
    )

    # Start delayed drain and sweeper coroutines
    drain_task = asyncio.create_task(_drain_delayed(client))
    sweeper_task = asyncio.create_task(run_sweeper(_shutdown))

    # Track in-flight tasks for graceful shutdown
    in_flight: set[asyncio.Task] = set()

    # -- Main BLPOP loop with concurrent dispatch --
    while not _shutdown.is_set():
        try:
            popped = await client.blpop(QUEUE_KEY, timeout=POP_TIMEOUT)
        except Exception:
            log.exception("worker.redis_pop_failed")
            await asyncio.sleep(2)
            continue
        if popped is None:
            # Clean up completed tasks
            done = {t for t in in_flight if t.done()}
            in_flight -= done
            continue

        _, raw = popped
        try:
            job = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("worker.bad_payload", raw=raw[:200])
            continue

        # Dispatch with semaphore-controlled concurrency
        task = asyncio.create_task(
            _process_with_semaphore(job, sem, client, worker_state)
        )
        in_flight.add(task)
        task.add_done_callback(in_flight.discard)

    # -- Graceful shutdown --
    log.info("worker.draining", in_flight=len(in_flight))
    worker_state.ready = False

    # Cancel delayed drain and sweeper
    drain_task.cancel()
    sweeper_task.cancel()
    try:
        await asyncio.gather(drain_task, sweeper_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass

    # Stop file watcher if hot_reload is enabled
    if settings.worker_hot_reload:
        try:
            from helix.core.watcher import stop_watcher
            await stop_watcher()
        except Exception:
            log.exception("worker.watcher_stop_failed")

    # Wait for in-flight jobs (with timeout)
    if in_flight:
        done, pending = await asyncio.wait(in_flight, timeout=30)
        if pending:
            log.warning("worker.force_cancel", count=len(pending))
            for t in pending:
                t.cancel()

    # Cleanup
    await client.aclose()
    await health_runner.cleanup()
    await close_checkpointer()
    log.info("worker.stopped", processed=worker_state.processed, failed=worker_state.failed)


if __name__ == "__main__":
    asyncio.run(main())
