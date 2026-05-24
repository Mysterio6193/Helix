"""Background optimization worker — evaluates rules and executes auto-actions."""
import asyncio
from datetime import datetime

from helix.core.db import AsyncSessionLocal
from helix.core.logging import get_logger
from helix.intelligence.rules_engine import RulesEngine
from helix.intelligence.actions import ActionExecutor, ApprovalQueue
from helix.intelligence.triggers import process_signal_triggers
from helix.models.intelligence import IntelligenceSignal

log = get_logger(__name__)


async def _process_workspace(session, workspace):
    """Process a single workspace for optimization rules and signals."""
    log.info("evaluating_optimization_rules", workspace=str(workspace.id))

    engine = RulesEngine(session)
    triggered = await engine.evaluate_all_rules(workspace.id)

    executed = 0
    pending = 0

    for trigger in triggered:
        if trigger["approval_required"]:
            queue = ApprovalQueue(session)
            await queue.create_approval_request(
                workspace.id,
                trigger["rule_id"],
                trigger["rule_name"],
                trigger["actions"],
                trigger["context"],
            )
            pending += 1
        else:
            executor = ActionExecutor(session)
            await executor.execute_actions(
                trigger["actions"],
                workspace.id,
                None,
                trigger["context"],
            )
            executed += 1

    await session.commit()
    log.info("optimization_evaluation_complete",
            triggered=len(triggered),
            executed=executed,
            pending=pending)

    # Process unprocessed signals for trigger automations
    signals_result = await session.execute(
        select(IntelligenceSignal)
        .where(
            IntelligenceSignal.workspace_id == workspace.id,
            IntelligenceSignal.processed == False,
        )
        .order_by(IntelligenceSignal.created_at)
        .limit(10)
    )
    unprocessed_signals = signals_result.scalars().all()

    triggered_automations = []
    for signal in unprocessed_signals:
        results = await process_signal_triggers(session, signal)
        triggered_automations.extend(results)
        signal.processed = True

    if triggered_automations:
        log.info("signal_triggers_processed",
                count=len(triggered_automations),
                automations=[t["automation_id"] for t in triggered_automations])

    await session.commit()


async def run_optimization_worker():
    """Main worker loop — evaluates optimization rules every 5 minutes."""
    log.info("optimization_worker_started")

    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Get all workspaces
                from sqlalchemy import select
                from helix.models.organization import Workspace
                result = await session.execute(select(Workspace))
                workspaces = result.scalars().all()

                log.info("optimization_processing_workspaces", count=len(workspaces))

                for workspace in workspaces:
                    try:
                        await _process_workspace(session, workspace)
                    except Exception:
                        log.exception("workspace_processing_failed", workspace=str(workspace.id))

        except Exception as e:
            log.error("optimization_worker_error", error=str(e))

        # Run every 5 minutes
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(run_optimization_worker())
