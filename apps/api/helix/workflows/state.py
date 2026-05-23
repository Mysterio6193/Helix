"""Shared LangGraph state contract for every Helix workflow.

Every workflow operates on a single `HelixState` TypedDict that flows through agent
nodes. Reducers (Annotated[list, operator.add]) let parallel nodes append to lists
without clobbering. Outputs are flushed to the DB via `WorkflowRun`/`Task`/`Asset`
rows + Redis pubsub events.
"""
from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, TypedDict
from uuid import UUID


@dataclass
class RunContext:
    """Immutable inputs to a workflow run."""

    run_id: UUID
    brand_id: UUID
    workspace_id: UUID
    workflow: str  # e.g. "brand_identity_foundation"
    inputs: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    user_id: UUID | None = None
    parent_run_id: UUID | None = None


@dataclass
class StepRecord:
    """Lightweight record of a single agent/skill step within a run."""

    step: str
    agent: str
    skill: str | None
    started_at: float
    ended_at: float | None
    status: str  # "running" | "ok" | "error"
    cost_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    output_summary: str | None = None
    error: str | None = None
    artifact_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class HelixState(TypedDict, total=False):
    """Mutable state shared across LangGraph nodes.

    Lists use `operator.add` reducers so parallel branches can append.
    Dicts use replacement (last writer wins) for namespaced shared scratchpad.
    """

    # Identity
    run_id: str
    brand_id: str
    workspace_id: str
    workflow: str
    user_id: str | None

    # Inputs / config
    inputs: dict[str, Any]
    config: dict[str, Any]

    # Brand context (loaded once at run start)
    brand_context: dict[str, Any]

    # Memory retrieval results
    memory_hits: list[dict[str, Any]]

    # Design system selection
    design_system: dict[str, Any]
    design_school: str | None

    # Creative briefs / strategy artifacts
    strategy: dict[str, Any]
    brief: dict[str, Any]
    plan: list[dict[str, Any]]

    # Copy outputs (keyed by purpose: tagline, headline, body, captions, etc.)
    copy: dict[str, Any]

    # Visual outputs - asset rows by purpose key
    visuals: Annotated[list[dict[str, Any]], operator.add]

    # Critic feedback chains
    critiques: Annotated[list[dict[str, Any]], operator.add]

    # Iteration counters
    iterations: dict[str, int]

    # Step history (every agent appends one StepRecord-ish dict)
    steps: Annotated[list[dict[str, Any]], operator.add]

    # Persisted artifacts
    asset_ids: Annotated[list[str], operator.add]

    # Lineage edges (parent -> child)
    lineage: Annotated[list[dict[str, str]], operator.add]

    # Final outputs (workflow-specific payload)
    output: dict[str, Any]

    # Errors (non-fatal accumulated)
    errors: Annotated[list[dict[str, Any]], operator.add]

    # Cost ledger
    total_cost_usd: float
    total_tokens_in: int
    total_tokens_out: int


def initial_state(ctx: RunContext) -> HelixState:
    """Build a clean initial state dict from a RunContext."""
    return HelixState(
        run_id=str(ctx.run_id),
        brand_id=str(ctx.brand_id),
        workspace_id=str(ctx.workspace_id),
        workflow=ctx.workflow,
        user_id=str(ctx.user_id) if ctx.user_id else None,
        inputs=dict(ctx.inputs),
        config=dict(ctx.config),
        brand_context={},
        memory_hits=[],
        design_system={},
        design_school=None,
        strategy={},
        brief={},
        plan=[],
        copy={},
        visuals=[],
        critiques=[],
        iterations={},
        steps=[],
        asset_ids=[],
        lineage=[],
        output={},
        errors=[],
        total_cost_usd=0.0,
        total_tokens_in=0,
        total_tokens_out=0,
    )
