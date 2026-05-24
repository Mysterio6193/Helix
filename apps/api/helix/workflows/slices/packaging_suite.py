"""Slice 2: Packaging Suite.

Graph:
   orchestrator -> load_prior -> [pizza_box, pasta_bowl, coffee_cup, delivery_bag, sticker_pack]
                              -> critic -> (revise_packaging | finalize) -> END

Each packaging node runs `design_packaging` for one SKU. They fan out in parallel
after the prior brand-identity context is loaded, join at the critic, and either
revise (re-runs the SKU branch flagged by the critic) or finalize. The critic may
issue one revision per slice.

The slice expects the upstream brand_identity_foundation outputs to be carried in
the run's `inputs` payload — either inline (`inputs.strategy`, `inputs.design_system`,
`inputs.logos`, `inputs.copy`) or by `inputs.from_run_id` (left as a stub here; the
API caller is responsible for materializing the context in `inputs.*` for now).
"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from helix.agents.base import AgentContext
from helix.agents.critic import CriticAgent
from helix.agents.orchestrator import OrchestratorAgent
from helix.agents.packaging_designer import PackagingDesignerAgent
from helix.core.logging import get_logger
from helix.core.observability import traced_node
from helix.workflows.runner import register_workflow
from helix.workflows.state import HelixState

log = get_logger(__name__)


SLICE_NAME = "packaging_suite"
MAX_REVISIONS = 3

# Default SKU set — restaurant-launch core kit. Caller can override via
# `inputs.skus = [...]`.
DEFAULT_SKUS: list[str] = [
    "pizza_box_12in",
    "pasta_bowl_kraft",
    "cup_12oz",
    "delivery_bag",
    "sticker_pack",
]


def _step(
    name: str,
    agent: str,
    skill: str | None,
    ok: bool,
    started: float,
    summary: str = "",
    artifact_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "step": name,
        "agent": agent,
        "skill": skill,
        "started_at": started,
        "ended_at": time.time(),
        "status": "ok" if ok else "error",
        "output_summary": summary,
        "artifact_ids": artifact_ids or [],
    }


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

@traced_node("orchestrate")
async def _orchestrator_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await OrchestratorAgent().run(AgentContext(state=dict(state)))
    return {
        **res.patch,
        "steps": [_step("orchestrate", "orchestrator", None, res.ok, started, "router")],
    }


@traced_node("load_prior")
async def _load_prior_node(state: HelixState) -> dict[str, Any]:
    """Hydrate upstream brand-identity context into state.

    The packaging_designer agent reads `state["strategy"]`, `state["design_system"]`,
    `state["copy"]`, and `state["visuals"]` (for logos). The caller passes those into
    `inputs` so we copy them onto the state root for downstream nodes.
    """
    started = time.time()
    inputs = state.get("inputs", {}) or {}
    patch: dict[str, Any] = {}
    if inputs.get("strategy"):
        patch["strategy"] = inputs["strategy"]
    if inputs.get("design_system"):
        patch["design_system"] = inputs["design_system"]
    if inputs.get("design_school"):
        patch["design_school"] = inputs["design_school"]
    if inputs.get("copy"):
        patch["copy"] = inputs["copy"]
    if inputs.get("logos"):
        # Carry approved logos into `visuals` so the agent's logo filter still works.
        patch["visuals"] = [
            {**item, "purpose": item.get("purpose", "logo")} for item in inputs["logos"]
        ]
    return {
        **patch,
        "steps": [_step("load_prior", "orchestrator", None, True, started, "hydrated prior identity")],
    }


def _make_sku_node(sku: str):
    @traced_node(f"design_{sku}")
    async def _node(state: HelixState) -> dict[str, Any]:
        started = time.time()
        res = await PackagingDesignerAgent().run(
            AgentContext(state=dict(state), extra={"sku": sku})
        )
        return {
            **res.patch,
            "steps": [
                _step(
                    f"design_{sku}",
                    "packaging_designer",
                    "design_packaging",
                    res.ok,
                    started,
                    f"sku={sku}",
                    res.artifact_ids,
                )
            ],
            "errors": [] if res.ok else [{"stage": f"packaging:{sku}", "error": res.error}],
        }

    _node.__name__ = f"_sku_node_{sku}"
    return _node


@traced_node("critique_packaging")
async def _critic_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    # Pull only the packaging visuals (purpose starts with "packaging:") for the critic.
    packaging_visuals = [
        v for v in state.get("visuals", []) if str(v.get("purpose", "")).startswith("packaging:")
    ]
    res = await CriticAgent().run(
        AgentContext(
            state=dict(state),
            extra={
                "target": "packaging_suite",
                "candidate": {
                    "design_system": state.get("design_system", {}),
                    "strategy": state.get("strategy", {}),
                    "packaging": packaging_visuals,
                },
            },
        )
    )
    iters = dict(state.get("iterations", {}))
    iters["critic_packaging"] = iters.get("critic_packaging", 0) + 1
    return {
        **res.patch,
        "iterations": iters,
        "steps": [_step("critique_packaging", "critic", "critique_output", res.ok, started)],
    }


def _route_after_critic(state: HelixState) -> str:
    critiques = state.get("critiques", [])
    if not critiques:
        return "finalize"
    last = critiques[-1]
    verdict = last.get("verdict", "accept")
    iters = state.get("iterations", {}).get("critic_packaging", 0)
    if verdict == "revise" and iters <= MAX_REVISIONS:
        target_sku = last.get("target_sku") or last.get("target_branch")
        skus = state.get("inputs", {}).get("skus") or DEFAULT_SKUS
        if target_sku in skus:
            return f"revise_{target_sku}"
        # Fall back to revising the first SKU if the critic didn't pick one.
        return f"revise_{skus[0]}"
    return "finalize"


@traced_node("finalize")
async def _finalize_node(state: HelixState) -> dict[str, Any]:
    skus = state.get("inputs", {}).get("skus") or DEFAULT_SKUS
    packaging_visuals = [
        v for v in state.get("visuals", []) if str(v.get("purpose", "")).startswith("packaging:")
    ]
    by_sku: dict[str, list[dict[str, Any]]] = {sku: [] for sku in skus}
    for v in packaging_visuals:
        sku = v.get("sku") or v.get("purpose", "").split(":", 1)[-1]
        by_sku.setdefault(sku, []).append(v)

    output = dict(state.get("output", {}))
    output["packaging_suite"] = {
        "skus": skus,
        "by_sku": {
            sku: [{"asset_id": v.get("asset_id"), "storage_key": v.get("storage_key")} for v in vs]
            for sku, vs in by_sku.items()
        },
        "total_assets": sum(len(vs) for vs in by_sku.values()),
    }
    return {"output": output}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph():
    g = StateGraph(HelixState)
    g.add_node("orchestrate", _orchestrator_node)
    g.add_node("load_prior", _load_prior_node)

    for sku in DEFAULT_SKUS:
        g.add_node(sku, _make_sku_node(sku))
        g.add_node(f"revise_{sku}", _make_sku_node(sku))

    g.add_node("critique", _critic_node)
    g.add_node("finalize", _finalize_node)

    g.add_edge(START, "orchestrate")
    g.add_edge("orchestrate", "load_prior")

    # Fan-out: every SKU starts after prior context is loaded.
    for sku in DEFAULT_SKUS:
        g.add_edge("load_prior", sku)
        g.add_edge(sku, "critique")
        # A revised SKU rejoins the critic.
        g.add_edge(f"revise_{sku}", "critique")

    revision_map: dict[str, str] = {f"revise_{sku}": f"revise_{sku}" for sku in DEFAULT_SKUS}
    revision_map["finalize"] = "finalize"
    g.add_conditional_edges("critique", _route_after_critic, revision_map)

    g.add_edge("finalize", END)
    return g.compile()


_GRAPH = _build_graph()


async def execute(state: HelixState) -> HelixState:
    """Run the compiled graph and return the final state dict."""
    final = await _GRAPH.ainvoke(state)
    return final  # type: ignore[return-value]


register_workflow(SLICE_NAME, execute)
