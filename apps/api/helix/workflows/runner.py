"""Workflow runner — compiles a LangGraph for a slice, executes, persists.

Workflow handlers are registered by slice name (e.g. "brand_identity_foundation").
Each handler returns a compiled `StateGraph` ready to invoke with a HelixState.
"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from helix.core.db import session_factory
from helix.core.langfuse_client import get_langfuse
from helix.core.langfuse_client import trace as lf_trace
from helix.core.logging import get_logger
from helix.core.observability import score_trace
from helix.skills.learning import extract_learning
from helix.skills.reflection import reflect_on_run
from helix.workflows.helpers import (
    emit_event,
    load_initial_brand_context,
    mark_run_status,
)
from helix.workflows.state import HelixState, RunContext, initial_state

log = get_logger(__name__)


# Slice-name -> async callable that builds + invokes the LangGraph and returns
# the final HelixState dict.
WorkflowExecutor = Callable[[HelixState, dict], Awaitable[HelixState]]
_WORKFLOWS: dict[str, WorkflowExecutor] = {}


def register_workflow(name: str, executor: WorkflowExecutor) -> None:
    _WORKFLOWS[name] = executor
    log.info("workflow_registered", name=name)


def list_workflows() -> list[str]:
    return list(_WORKFLOWS.keys())


async def execute_run(ctx: RunContext) -> HelixState:
    """Top-level entrypoint: marks run running, loads brand context, runs slice,
    flushes learnings + cost, marks done.
    """
    executor = _WORKFLOWS.get(ctx.workflow)
    if executor is None:
        raise ValueError(f"workflow not registered: {ctx.workflow}")

    state: HelixState = initial_state(ctx)
    started = time.time()

    # Langfuse root trace for the entire run
    langfuse_trace = lf_trace(
        name=f"run:{ctx.workflow}",
        run_id=str(ctx.run_id),
        brand_id=str(ctx.brand_id),
        workflow=ctx.workflow,
    )
    if langfuse_trace:
        state["langfuse_trace_id"] = langfuse_trace.id

    async with session_factory() as session:
        await mark_run_status(session, run_id=ctx.run_id, status="running")
        await session.commit()

    await emit_event(
        run_id=ctx.run_id,
        kind="run.started",
        payload={"workflow": ctx.workflow, "inputs": dict(ctx.inputs)},
    )

    # Brand context
    try:
        state["brand_context"] = await load_initial_brand_context(state)
    except Exception as exc:  # pragma: no cover
        log.exception("brand_context_load_failed")
        state["errors"] = list(state.get("errors", [])) + [{"stage": "brand_context", "error": str(exc)}]

    # Execute workflow graph
    error: str | None = None
    try:
        config = {"configurable": {"thread_id": str(ctx.run_id)}}
        # Let the executor handle resume logic internally or here?
        # Actually, if we pass state=None, ainvoke will just resume.
        # But we need to do it at the executor level, or we just pass the initial state and executor decides.
        state = await executor(state, config)
    except Exception as exc:
        log.exception("workflow_execution_failed", workflow=ctx.workflow)
        error = f"{type(exc).__name__}: {exc}"
        state["errors"] = list(state.get("errors", [])) + [{"stage": "execute", "error": error}]

    duration_ms = int((time.time() - started) * 1000)
    final_status = "failed" if error else "succeeded"

    # Persist learnings (closed-loop)
    try:
        learnings = await reflect_on_run(state)
        async with session_factory() as session:
            for lrn in learnings:
                await extract_learning(
                    session,
                    skill_name=lrn["skill_name"],
                    workflow_run_id=lrn["workflow_run_id"],
                    brand_id=lrn["brand_id"],
                    trigger_context=lrn["trigger_context"],
                    prompt_delta=lrn["prompt_delta"],
                    success_markers=lrn["success_markers"],
                    score=lrn["score"],
                    context_embedding=state.get("brand_context", {}).get("embedding"),
                )
            await mark_run_status(
                session, run_id=ctx.run_id, status=final_status, error=error
            )
            await session.commit()

        # Check for promotion if brand is set and run succeeded
        if ctx.brand_id and final_status == "succeeded":
            from helix.skills.promotion import promote_specialization
            unique_skills = {lrn["skill_name"] for lrn in learnings if lrn.get("skill_name")}
            for s_name in unique_skills:
                try:
                    async with session_factory() as promote_session:
                        spec = await promote_specialization(promote_session, s_name, ctx.brand_id)
                        if spec:
                            log.info("workflow.skill_promoted", parent=s_name, specialization=spec.name, brand_id=str(ctx.brand_id))
                        await promote_session.commit()
                except Exception as exc:
                    log.exception("workflow.promotion_failed", skill=s_name, brand_id=str(ctx.brand_id), error=str(exc))
    except Exception:  # pragma: no cover
        log.exception("learning_or_status_persist_failed")

    await emit_event(
        run_id=ctx.run_id,
        kind="run.completed" if not error else "run.failed",
        payload={
            "status": final_status,
            "duration_ms": duration_ms,
            "total_cost_usd": state.get("total_cost_usd", 0.0),
            "asset_count": len(state.get("asset_ids", [])),
            "error": error,
        },
    )

    # Flush Langfuse scores and trace
    trace_id = state.get("langfuse_trace_id")
    if trace_id:
        score_trace(trace_id, "run_success", 1.0 if not error else 0.0)
        score_trace(trace_id, "run_cost_usd", state.get("total_cost_usd", 0.0) or 0.0)
        score_trace(trace_id, "run_duration_ms", float(duration_ms))
        lf = get_langfuse()
        if lf:
            try:
                lf.flush()
            except Exception:
                log.debug("langfuse_flush_failed", exc_info=True)

    return state
