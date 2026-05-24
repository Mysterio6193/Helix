"""Slice 5: Launch Campaign.

Graph:
   orchestrator -> load_prior -> launch_manager -> critic -> (revise_launch | finalize) -> END

`launch_manager` invokes the `orchestrate_launch_campaign` skill which assembles:
  - launch calendar (T-14 to T+14)
  - 4 email drafts (teaser / announce / day-of / follow-up)
  - press kit (one_liner / short_bio / long_bio / quotes / press contact)
  - ad copy variants (Meta + Google + TikTok)
  - rollout phases + success metrics

This slice is intentionally a single-skill composer. The plan layer expected
prior visual / packaging / website / social work to already exist in the
brand context — the campaign is *plan + copy*, not new visuals.
"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from helix.agents.base import AgentContext
from helix.agents.critic import CriticAgent
from helix.agents.launch_manager import LaunchManagerAgent
from helix.agents.orchestrator import OrchestratorAgent
from helix.core.logging import get_logger
from helix.core.observability import traced_node
from helix.workflows.runner import register_workflow
from helix.workflows.state import HelixState

log = get_logger(__name__)


SLICE_NAME = "launch_campaign"
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
            {**item, "purpose": item.get("purpose", "logo")} for item in inputs["logos"]
        ]
    return {
        **patch,
        "steps": [_step("load_prior", "orchestrator", None, True, started, "hydrated prior identity")],
    }


@traced_node("orchestrate_launch")
async def _launch_manager_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    inputs = state.get("inputs", {}) or {}
    res = await LaunchManagerAgent().run(
        AgentContext(
            state=dict(state),
            extra={
                "channels": inputs.get("channels", ["email", "social", "press", "paid"]),
            },
        )
    )
    summary = ""
    if res.ok:
        skill_res = res.skill_results[0] if res.skill_results else None
        counts = (skill_res.outputs.get("counts") if skill_res else {}) or {}
        summary = (
            f"calendar={counts.get('calendar', 0)} "
            f"emails={counts.get('emails', 0)} "
            f"ads={counts.get('meta_ads', 0)+counts.get('google_ads', 0)+counts.get('tiktok_ads', 0)}"
        )
    return {
        **res.patch,
        "steps": [
            _step(
                "orchestrate_launch",
                "launch_manager",
                "orchestrate_launch_campaign",
                res.ok,
                started,
                summary,
                res.artifact_ids,
            )
        ],
        "errors": [] if res.ok else [{"stage": "launch", "error": res.error}],
    }


@traced_node("critique_launch")
async def _critic_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    launch = (state.get("output") or {}).get("launch_campaign") or {}
    candidate = {
        "design_system": state.get("design_system", {}),
        "strategy": state.get("strategy", {}),
        "calendar_count": len(launch.get("calendar") or []),
        "emails": launch.get("emails", []),
        "press_kit": launch.get("press_kit", {}),
        "ads": launch.get("ads", {}),
        "rollout": launch.get("rollout", {}),
    }
    res = await CriticAgent().run(
        AgentContext(
            state=dict(state),
            extra={"target": "launch", "candidate": candidate},
        )
    )
    iters = dict(state.get("iterations", {}))
    iters["critic_launch"] = iters.get("critic_launch", 0) + 1
    return {
        **res.patch,
        "iterations": iters,
        "steps": [_step("critique_launch", "critic", "critique_output", res.ok, started)],
    }


def _route_after_critic(state: HelixState) -> str:
    critiques = state.get("critiques", [])
    if not critiques:
        return "finalize"
    last = critiques[-1]
    verdict = last.get("verdict", "accept")
    iters = state.get("iterations", {}).get("critic_launch", 0)
    if verdict == "revise" and iters <= MAX_REVISIONS:
        return "revise_launch"
    return "finalize"


@traced_node("finalize")
async def _finalize_node(state: HelixState) -> dict[str, Any]:
    launch = (state.get("output") or {}).get("launch_campaign") or {}
    output = dict(state.get("output", {}))
    output["launch_summary"] = {
        "calendar_count": len(launch.get("calendar") or []),
        "email_count": len(launch.get("emails") or []),
        "press_quote_count": len((launch.get("press_kit") or {}).get("quotes") or []),
        "ad_variant_count": (
            len((launch.get("ads") or {}).get("meta") or [])
            + len((launch.get("ads") or {}).get("google") or [])
            + len((launch.get("ads") or {}).get("tiktok") or [])
        ),
        "rollout_phases": [
            p.get("name") for p in (launch.get("rollout") or {}).get("phases", [])
            if isinstance(p, dict)
        ],
        "channels": launch.get("channels", []),
        "launch_date": launch.get("launch_date"),
    }
    return {"output": output}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph():
    g = StateGraph(HelixState)
    g.add_node("orchestrate", _orchestrator_node)
    g.add_node("load_prior", _load_prior_node)
    g.add_node("build_launch", _launch_manager_node)
    g.add_node("revise_launch", _launch_manager_node)
    g.add_node("critique", _critic_node)
    g.add_node("finalize", _finalize_node)

    g.add_edge(START, "orchestrate")
    g.add_edge("orchestrate", "load_prior")
    g.add_edge("load_prior", "build_launch")
    g.add_edge("build_launch", "critique")
    g.add_edge("revise_launch", "critique")
    g.add_conditional_edges(
        "critique",
        _route_after_critic,
        {"revise_launch": "revise_launch", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)
    return g.compile()


_GRAPH = _build_graph()


async def execute(state: HelixState) -> HelixState:
    """Run the compiled graph and return the final state dict."""
    final = await _GRAPH.ainvoke(state)
    return final  # type: ignore[return-value]


register_workflow(SLICE_NAME, execute)
