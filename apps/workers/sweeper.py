"""Helix Background Sweeper.

Runs periodically to:
1. Fire ScheduledJobs whose next_run_at <= now()
2. Mark AgentSessions offline if last_heartbeat_at is too old
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from croniter import croniter
from sqlalchemy import select

from helix.core.db import session_factory
from helix.models.runtime import ScheduledJob, AgentSession
from helix.services.run_queue import enqueue_run

log = logging.getLogger("helix.worker.sweeper")

async def sweep_jobs():
    """Poll for due scheduled jobs and enqueue them."""
    try:
        now = datetime.now(timezone.utc)
        now_naive = now.replace(tzinfo=None)

        async with session_factory() as session:
            # Find due jobs
            q = select(ScheduledJob).where(
                ScheduledJob.enabled == True,
                ScheduledJob.next_run_at <= now_naive
            )
            result = await session.execute(q)
            jobs = result.scalars().all()

            for job in jobs:
                log.info("sweeper.fire_job", job_id=str(job.id), workflow=job.workflow)
                
                # Enqueue a run
                run = await enqueue_run(
                    brand_id=job.brand_id,
                    workspace_id=job.workspace_id,
                    workflow=job.workflow,
                    inputs=job.inputs,
                    config=job.config,
                    user_id=job.created_by,
                )

                # Compute next run
                next_run = None
                if job.cron:
                    try:
                        cron = croniter(job.cron, now)
                        next_run = cron.get_next(datetime).replace(tzinfo=None)
                    except Exception:
                        log.exception("sweeper.cron_error", job_id=str(job.id))
                elif job.interval_s:
                    next_run = now_naive + timedelta(seconds=job.interval_s)

                job.last_run_at = now_naive
                job.last_run_id = run.id
                job.next_run_at = next_run
            
            if jobs:
                await session.commit()
    except Exception:
        log.exception("sweeper.jobs_sweep_error")


async def sweep_sessions():
    """Check agent session heartbeats and mark them offline if they missed heartbeats."""
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        async with session_factory() as session:
            q = select(AgentSession).where(AgentSession.status.in_(["running", "active"]))
            result = await session.execute(q)
            agent_sessions = result.scalars().all()

            changed = False
            for agent in agent_sessions:
                # If they missed 2 heartbeats, consider them offline
                cutoff = now - timedelta(seconds=agent.heartbeat_interval_s * 2 + 10)
                
                if agent.last_heartbeat_at and agent.last_heartbeat_at < cutoff:
                    log.warning("sweeper.session_offline", session_id=str(agent.id))
                    agent.status = "offline"
                    agent.error = "Missed heartbeats; marked offline by sweeper"
                    changed = True
                elif not agent.last_heartbeat_at and agent.created_at < cutoff:
                    log.warning("sweeper.session_never_started", session_id=str(agent.id))
                    agent.status = "offline"
                    agent.error = "Never sent initial heartbeat; marked offline by sweeper"
                    changed = True

            if changed:
                await session.commit()
    except Exception:
        log.exception("sweeper.sessions_sweep_error")


async def run_sweeper(shutdown_event: asyncio.Event):
    """Main sweeper loop."""
    log.info("sweeper.started")
    while not shutdown_event.is_set():
        await sweep_jobs()
        await sweep_sessions()
        
        # Sleep in small increments to respond to shutdown quickly
        for _ in range(10):
            if shutdown_event.is_set():
                break
            await asyncio.sleep(1)
    
    log.info("sweeper.stopped")
