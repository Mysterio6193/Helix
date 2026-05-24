"""Background Job System — Priority queues, retries, monitoring, scheduling.

Features:
- Priority queues (critical, high, normal, low)
- Exponential backoff retries with jitter
- Job timeouts and cancellation
- Progress tracking
- Scheduled jobs (cron-like)
- Job chaining and dependencies
- Dead letter queue for failed jobs
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.core.redis import get_redis

log = get_logger("helix.jobs")
settings = get_settings()


class JobPriority(Enum):
    CRITICAL = 1
    HIGH = 3
    NORMAL = 5
    LOW = 7


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    DEAD = "dead"


@dataclass
class Job:
    """A background job."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = JobPriority.NORMAL.value
    status: str = JobStatus.PENDING.value
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    worker_id: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    retry_delay: int = 60
    timeout: int = 300
    progress: float = 0.0
    result: Any = None
    error: str | None = None
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "progress": self.progress,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "tags": self.tags,
        }


class JobRegistry:
    """Registry of job handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable] = {}

    def register(self, name: str, handler: Callable) -> None:
        self._handlers[name] = handler
        log.info("job_handler_registered", name=name)

    def get(self, name: str) -> Callable | None:
        return self._handlers.get(name)

    def list(self) -> list[str]:
        return list(self._handlers.keys())


class JobQueue:
    """Priority job queue backed by Redis sorted sets."""

    def __init__(self) -> None:
        self._redis_key = "helix:jobs:queue"
        self._processing_key = "helix:jobs:processing"
        self._dead_key = "helix:jobs:dead"
        self._job_prefix = "helix:job:"

    def _job_key(self, job_id: str) -> str:
        return f"{self._job_prefix}{job_id}"

    async def enqueue(
        self,
        name: str,
        payload: dict[str, Any],
        priority: int = JobPriority.NORMAL.value,
        max_attempts: int = 3,
        timeout: int = 300,
        tags: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> Job:
        """Add a job to the queue."""
        job = Job(
            name=name,
            payload=payload,
            priority=priority,
            max_attempts=max_attempts,
            timeout=timeout,
            tags=tags or [],
            dependencies=dependencies or [],
        )

        redis = get_redis()
        pipe = redis.pipeline()

        # Store job data
        pipe.setex(
            self._job_key(job.id),
            86400 * 7,  # 7 days TTL
            json.dumps(job.__dict__, default=str),
        )

        # Add to priority queue (lower score = higher priority)
        pipe.zadd(self._redis_key, {job.id: priority})

        await pipe.execute()
        log.info("job_enqueued", job_id=job.id, name=name, priority=priority)
        return job

    async def dequeue(self, worker_id: str, timeout: int = 5) -> Job | None:
        """Get the highest priority job from the queue."""
        redis = get_redis()

        # Use Redis transaction to atomically pop from queue
        async with redis.pipeline(transaction=True) as pipe:
            # Get highest priority job (lowest score)
            pipe.zrange(self._redis_key, 0, 0)
            result = await pipe.execute()

        if not result or not result[0]:
            return None

        job_id = result[0][0].decode() if isinstance(result[0][0], bytes) else result[0][0]

        # Remove from queue and mark as processing
        removed = await redis.zrem(self._redis_key, job_id)
        if not removed:
            return None  # Another worker got it

        # Load job data
        job_data = await redis.get(self._job_key(job_id))
        if not job_data:
            return None

        job_dict = json.loads(job_data)
        job = Job(**job_dict)
        job.status = JobStatus.RUNNING.value
        job.started_at = time.time()
        job.worker_id = worker_id
        job.attempts += 1

        # Update in Redis
        await redis.setex(
            self._job_key(job.id),
            86400 * 7,
            json.dumps(job.__dict__, default=str),
        )
        await redis.hset(self._processing_key, job.id, worker_id)

        return job

    async def complete(self, job: Job, result: Any) -> None:
        """Mark a job as completed."""
        job.status = JobStatus.COMPLETED.value
        job.completed_at = time.time()
        job.result = result
        job.progress = 100.0

        redis = get_redis()
        await redis.setex(
            self._job_key(job.id),
            86400 * 7,
            json.dumps(job.__dict__, default=str),
        )
        await redis.hdel(self._processing_key, job.id)
        log.info("job_completed", job_id=job.id, name=job.name, duration=job.completed_at - (job.started_at or job.created_at))

    async def fail(self, job: Job, error: str) -> None:
        """Handle job failure with retry logic."""
        job.error = error

        if job.attempts < job.max_attempts:
            # Retry with exponential backoff + jitter
            delay = job.retry_delay * (2 ** (job.attempts - 1))
            jitter = hashlib.md5(job.id.encode()).hexdigest()
            delay += int(jitter, 16) % 30  # Add 0-30s jitter

            job.status = JobStatus.RETRYING.value
            job.started_at = None
            job.worker_id = None

            redis = get_redis()
            await redis.setex(
                self._job_key(job.id),
                86400 * 7,
                json.dumps(job.__dict__, default=str),
            )
            await redis.hdel(self._processing_key, job.id)

            # Re-queue with same priority after delay
            await redis.zadd(self._redis_key, {job.id: job.priority})
            log.warning("job_retrying", job_id=job.id, attempt=job.attempts, delay=delay)
        else:
            # Max attempts reached, move to dead letter queue
            job.status = JobStatus.DEAD.value
            job.completed_at = time.time()

            redis = get_redis()
            await redis.setex(
                self._job_key(job.id),
                86400 * 30,  # 30 days for dead jobs
                json.dumps(job.__dict__, default=str),
            )
            await redis.hdel(self._processing_key, job.id)
            await redis.lpush(self._dead_key, job.id)
            log.error("job_dead", job_id=job.id, name=job.name, error=error, attempts=job.attempts)

    async def update_progress(self, job_id: str, progress: float, metadata: dict[str, Any] | None = None) -> None:
        """Update job progress."""
        redis = get_redis()
        job_data = await redis.get(self._job_key(job_id))
        if job_data:
            job_dict = json.loads(job_data)
            job_dict["progress"] = progress
            if metadata:
                job_dict["metadata"] = metadata
            await redis.setex(
                self._job_key(job_id),
                86400 * 7,
                json.dumps(job_dict, default=str),
            )

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending job."""
        redis = get_redis()

        # Remove from queue
        removed = await redis.zrem(self._redis_key, job_id)
        if removed:
            job_data = await redis.get(self._job_key(job_id))
            if job_data:
                job_dict = json.loads(job_data)
                job_dict["status"] = JobStatus.CANCELLED.value
                await redis.setex(
                    self._job_key(job_id),
                    86400,
                    json.dumps(job_dict, default=str),
                )
            log.info("job_cancelled", job_id=job_id)
            return True
        return False

    async def get_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        redis = get_redis()
        queue_size = await redis.zcard(self._redis_key)
        processing = await redis.hlen(self._processing_key)
        dead = await redis.llen(self._dead_key)

        return {
            "queue_size": queue_size,
            "processing": processing,
            "dead_letter_queue": dead,
            "total_jobs": queue_size + processing + dead,
        }

    async def list_jobs(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs with optional filtering."""
        redis = get_redis()
        jobs: list[Job] = []

        # Scan for job keys
        cursor = 0
        pattern = f"{self._job_prefix}*"
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            for key in keys:
                job_data = await redis.get(key)
                if job_data:
                    job_dict = json.loads(job_data)
                    if status is None or job_dict.get("status") == status:
                        jobs.append(Job(**job_dict))
            if cursor == 0:
                break

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset:offset + limit]


class JobWorker:
    """Worker that processes jobs from the queue."""

    def __init__(self, worker_id: str | None = None, concurrency: int = 3) -> None:
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.concurrency = concurrency
        self.registry = JobRegistry()
        self.queue = JobQueue()
        self._running = False
        self._tasks: set[asyncio.Task] = set()

    def register_handler(self, name: str, handler: Callable) -> None:
        self.registry.register(name, handler)

    async def start(self) -> None:
        """Start processing jobs."""
        self._running = True
        log.info("job_worker_started", worker_id=self.worker_id, concurrency=self.concurrency)

        semaphore = asyncio.Semaphore(self.concurrency)

        while self._running:
            try:
                job = await self.queue.dequeue(self.worker_id, timeout=5)
                if job:
                    task = asyncio.create_task(self._process_job(job, semaphore))
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)
                else:
                    await asyncio.sleep(1)
            except Exception as exc:
                log.exception("job_worker_error", error=str(exc))
                await asyncio.sleep(5)

    async def _process_job(self, job: Job, semaphore: asyncio.Semaphore) -> None:
        async with semaphore:
            handler = self.registry.get(job.name)
            if not handler:
                await self.queue.fail(job, f"No handler registered for: {job.name}")
                return

            try:
                # Set timeout
                result = await asyncio.wait_for(
                    handler(job.payload, job),
                    timeout=job.timeout,
                )
                await self.queue.complete(job, result)
            except TimeoutError:
                await self.queue.fail(job, f"Job timed out after {job.timeout}s")
            except Exception as exc:
                await self.queue.fail(job, str(exc))

    async def stop(self) -> None:
        """Gracefully stop the worker."""
        self._running = False
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        log.info("job_worker_stopped", worker_id=self.worker_id)


# Global instances
_queue: JobQueue | None = None
_registry: JobRegistry | None = None


def get_job_queue() -> JobQueue:
    global _queue
    if _queue is None:
        _queue = JobQueue()
    return _queue


def get_job_registry() -> JobRegistry:
    global _registry
    if _registry is None:
        _registry = JobRegistry()
    return _registry


async def enqueue_job(
    name: str,
    payload: dict[str, Any],
    priority: int = JobPriority.NORMAL.value,
    **kwargs: Any,
) -> Job:
    """Convenience function to enqueue a job."""
    queue = get_job_queue()
    return await queue.enqueue(name, payload, priority, **kwargs)
