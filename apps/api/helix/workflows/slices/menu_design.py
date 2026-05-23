"""Slice 6: Menu Design.

Graph:
   orchestrator -> load_prior -> menu_designer -> critic -> (revise_menu | finalize) -> END

`menu_designer` invokes the `design_menu_pack` skill which:
  - generates a structured menu (sections, items, prices, dietary tags)
  - writes a photography brief
  - renders N mockup images at the chosen print format
"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from helix.agents.base import AgentContext
from helix.agents.critic import CriticAgent
from helix.agents.menu_designer import MenuDesignerAgent
from helix.agents.orchestrator import OrchestratorAgent
from helix.core.logging import get_logger
from helix.core.observability import traced_node
from helix.workflows.runner import register_workflow
from helix.workflows.state import HelixState

log = get_logger(__name__)


SLICE_NAME = "menu_design"
MAX_REVISIONS = 3


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
        patch["visuals"] = [
            {**l, "purpose": l.get("purpose", "logo")} for l in inputs["logos"]
        ]
    return {
        **patch,
        "steps": [_step("load_prior", "orchestrator", None, True, started, "hydrated prior identity")],
    }


@traced_node("build_menu")
async def _menu_designer_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    inputs = state.get("inputs", {}) or {}
    res = await MenuDesignerAgent().run(
        AgentContext(
            state=dict(state),
            extra={
                "cuisine": inputs.get("cuisine"),
                "format": inputs.get("format", "a4_portrait"),
                "mockup_count": inputs.get("mockup_count", 3),
            },
        )
    )
    summary = ""
    if res.ok:
        skill_res = res.skill_results[0] if res.skill_results else None
        counts = (skill_res.outputs.get("counts") if skill_res else {}) or {}
        summary = f"sections={counts.get('sections', 0)} mockups={counts.get('mockups', 0)}"
    return {
        **res.patch,
        "steps": [
            _step(
                "build_menu",
                "menu_designer",
                "design_menu_pack",
                res.ok,
                started,
                summary,
                res.artifact_ids,
            )
        ],
        "errors": [] if res.ok else [{"stage": "menu", "error": res.error}],
    }


@traced_node("critique_menu")
async def _critic_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    menu_pack = (state.get("output") or {}).get("menu_pack") or {}
    visuals = state.get("visuals") or []
    mockups = [v for v in visuals if v.get("purpose") == "menu:mockup"]
    candidate = {
        "design_system": state.get("design_system", {}),
        "strategy": state.get("strategy", {}),
        "sections": menu_pack.get("sections", []),
        "photography_brief": menu_pack.get("photography_brief"),
        "format": menu_pack.get("format"),
        "mockup_count": len(mockups),
    }
    res = await CriticAgent().run(
        AgentContext(
            state=dict(state),
            extra={"target": "menu", "candidate": candidate},
        )
    )
    iters = dict(state.get("iterations", {}))
    iters["critic_menu"] = iters.get("critic_menu", 0) + 1
    return {
        **res.patch,
        "iterations": iters,
        "steps": [_step("critique_menu", "critic", "critique_output", res.ok, started)],
    }


def _route_after_critic(state: HelixState) -> str:
    critiques = state.get("critiques", [])
    if not critiques:
        return "finalize"
    last = critiques[-1]
    verdict = last.get("verdict", "accept")
    iters = state.get("iterations", {}).get("critic_menu", 0)
    if verdict == "revise" and iters <= MAX_REVISIONS:
        return "revise_menu"
    return "finalize"


@traced_node("finalize")
async def _finalize_node(state: HelixState) -> dict[str, Any]:
    menu_pack = (state.get("output") or {}).get("menu_pack") or {}
    visuals = state.get("visuals") or []
    output = dict(state.get("output", {}))
    output["menu_summary"] = {
        "section_count": len(menu_pack.get("sections") or []),
        "item_count": sum(
            len(s.get("items") or []) for s in (menu_pack.get("sections") or [])
            if isinstance(s, dict)
        ),
        "mockup_count": len([v for v in visuals if v.get("purpose") == "menu:mockup"]),
        "format": menu_pack.get("format"),
    }
    return {"output": output}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph():
    g = StateGraph(HelixState)
    g.add_node("orchestrate", _orchestrator_node)
    g.add_node("load_prior", _load_prior_node)
    g.add_node("build_menu", _menu_designer_node)
    g.add_node("revise_menu", _menu_designer_node)
    g.add_node("critique", _critic_node)
    g.add_node("finalize", _finalize_node)

    g.add_edge(START, "orchestrate")
    g.add_edge("orchestrate", "load_prior")
    g.add_edge("load_prior", "build_menu")
    g.add_edge("build_menu", "critique")
    g.add_edge("revise_menu", "critique")
    g.add_conditional_edges(
        "critique",
        _route_after_critic,
        {"revise_menu": "revise_menu", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)
    return g.compile()


_GRAPH = _build_graph()


async def execute(state: HelixState) -> HelixState:
    """Run the compiled graph and return the final state dict."""
    final = await _GRAPH.ainvoke(state)
    return final  # type: ignore[return-value]


register_workflow(SLICE_NAME, execute)
