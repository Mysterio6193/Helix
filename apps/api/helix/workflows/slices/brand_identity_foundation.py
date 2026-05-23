"""Slice 1: Brand Identity Foundation.

Graph:
   orchestrator -> brand_strategist -> creative_director -> [copywriter, visual_designer]
                                                          -> critic -> END

The copywriter + visual_designer run in parallel after the design school is selected,
join at the critic, and end. The critic may issue a "revise" verdict; the workflow
re-runs the failing branch once (max one revision loop per slice) before accepting.
"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from helix.agents.base import AgentContext
from helix.agents.brand_strategist import BrandStrategistAgent
from helix.agents.copywriter import CopywriterAgent
from helix.agents.creative_director import CreativeDirectorAgent
from helix.agents.critic import CriticAgent
from helix.agents.orchestrator import OrchestratorAgent
from helix.agents.visual_designer import VisualDesignerAgent
from helix.core.logging import get_logger
from helix.core.observability import traced_node
from helix.workflows.runner import register_workflow
from helix.workflows.state import HelixState

log = get_logger(__name__)


SLICE_NAME = "brand_identity_foundation"
MAX_REVISIONS = 3


def _step(name: str, agent: str, skill: str | None, ok: bool, started: float, summary: str = "") -> dict[str, Any]:
    return {
        "step": name,
        "agent": agent,
        "skill": skill,
        "started_at": started,
        "ended_at": time.time(),
        "status": "ok" if ok else "error",
        "output_summary": summary,
        "artifact_ids": [],
    }


@traced_node("orchestrate")
async def _orchestrator_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await OrchestratorAgent().run(AgentContext(state=dict(state)))
    return {
        **res.patch,
        "steps": [_step("orchestrate", "orchestrator", None, res.ok, started, "router")],
    }


@traced_node("strategy")
async def _strategy_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await BrandStrategistAgent().run(AgentContext(state=dict(state)))
    return {
        **res.patch,
        "steps": [_step("strategy", "brand_strategist", "brand_strategy_brief", res.ok, started)],
        "errors": [] if res.ok else [{"stage": "strategy", "error": res.error}],
    }


@traced_node("art_direction")
async def _direction_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await CreativeDirectorAgent().run(AgentContext(state=dict(state)))
    return {
        **res.patch,
        "steps": [_step("art_direction", "creative_director", "select_design_school", res.ok, started)],
        "errors": [] if res.ok else [{"stage": "art_direction", "error": res.error}],
    }


@traced_node("copy_taglines")
async def _copy_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await CopywriterAgent().run(
        AgentContext(state=dict(state), extra={"purpose": "taglines", "count": 6})
    )
    return {
        **res.patch,
        "steps": [_step("copy_taglines", "copywriter", "generate_taglines", res.ok, started)],
        "errors": [] if res.ok else [{"stage": "copy", "error": res.error}],
    }


@traced_node("logo_variants")
async def _visuals_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await VisualDesignerAgent().run(
        AgentContext(state=dict(state), extra={"purpose": "logo", "variant_count": 4})
    )
    return {
        **res.patch,
        "steps": [_step("logo_variants", "visual_designer", "design_logo", res.ok, started)],
        "errors": [] if res.ok else [{"stage": "visuals", "error": res.error}],
    }


@traced_node("critique")
async def _critic_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await CriticAgent().run(
        AgentContext(
            state=dict(state),
            extra={
                "target": "brand_identity",
                "candidate": {
                    "copy": state.get("copy", {}),
                    "visuals": state.get("visuals", []),
                    "design_system": state.get("design_system", {}),
                },
            },
        )
    )
    iters = dict(state.get("iterations", {}))
    iters["critic"] = iters.get("critic", 0) + 1
    return {
        **res.patch,
        "iterations": iters,
        "steps": [_step("critique", "critic", "critique_output", res.ok, started)],
    }


def _route_after_critic(state: HelixState) -> str:
    critiques = state.get("critiques", [])
    if not critiques:
        return "finalize"
    last = critiques[-1]
    verdict = last.get("verdict", "accept")
    iters = state.get("iterations", {}).get("critic", 0)
    if verdict == "revise" and iters <= MAX_REVISIONS:
        # Decide which branch to revise based on the critique's `target_branch`
        branch = last.get("target_branch", "visuals")
        return "revise_visuals" if branch == "visuals" else "revise_copy"
    return "finalize"


@traced_node("finalize")
async def _finalize_node(state: HelixState) -> dict[str, Any]:
    output = dict(state.get("output", {}))
    output["brand_identity"] = {
        "design_school": state.get("design_school"),
        "design_system_slug": state.get("design_system", {}).get("slug"),
        "tagline_options": state.get("copy", {}).get("taglines", {}).get("options", []),
        "logo_asset_ids": [
            v.get("asset_id") for v in state.get("visuals", []) if v.get("purpose") == "logo"
        ],
        "strategy": state.get("strategy", {}),
    }
    return {"output": output}


def _build_graph():
    g = StateGraph(HelixState)
    g.add_node("orchestrate", _orchestrator_node)
    g.add_node("strategy_generation", _strategy_node)
    g.add_node("art_direction", _direction_node)
    g.add_node("copy_generation", _copy_node)
    g.add_node("visuals_generation", _visuals_node)
    g.add_node("critique", _critic_node)
    g.add_node("revise_copy", _copy_node)
    g.add_node("revise_visuals", _visuals_node)
    g.add_node("finalize", _finalize_node)

    g.add_edge(START, "orchestrate")
    g.add_edge("orchestrate", "strategy_generation")
    g.add_edge("strategy_generation", "art_direction")
    # Fan-out to copy + visuals
    g.add_edge("art_direction", "copy_generation")
    g.add_edge("art_direction", "visuals_generation")
    # Both join into critique
    g.add_edge("copy_generation", "critique")
    g.add_edge("visuals_generation", "critique")
    # Critic conditionally routes
    g.add_conditional_edges(
        "critique",
        _route_after_critic,
        {"revise_copy": "revise_copy", "revise_visuals": "revise_visuals", "finalize": "finalize"},
    )
    # Revisions loop back through critic
    g.add_edge("revise_copy", "critique")
    g.add_edge("revise_visuals", "critique")
    g.add_edge("finalize", END)
    return g.compile()


_GRAPH = _build_graph()


async def execute(state: HelixState) -> HelixState:
    """Run the compiled graph and return the final state dict."""
    final = await _GRAPH.ainvoke(state)
    return final  # type: ignore[return-value]


register_workflow(SLICE_NAME, execute)
