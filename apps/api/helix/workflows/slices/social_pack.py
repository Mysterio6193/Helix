"""Slice 4: Social Pack.

Graph:
   orchestrator -> load_prior -> social_producer -> critic -> (revise_social | finalize) -> END

`social_producer` invokes the `build_social_pack` skill which:
  - generates a structured plan (captions / hashtags / bios / 14-day cadence)
  - renders N feed tiles (1024x1024)
  - renders M story templates (1024x1536)

The critic inspects the plan + a summary of the visual count. One revision is
allowed — if the critic rejects, the producer re-runs (the LLM plan call is
non-deterministic and image prompts will redraw on the same seed-by-slot scheme).
"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from helix.agents.base import AgentContext
from helix.agents.critic import CriticAgent
from helix.agents.orchestrator import OrchestratorAgent
from helix.agents.social_producer import SocialProducerAgent
from helix.core.logging import get_logger
from helix.core.observability import traced_node
from helix.workflows.runner import register_workflow
from helix.workflows.state import HelixState

log = get_logger(__name__)


SLICE_NAME = "social_pack"
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


@traced_node("build_social")
async def _social_producer_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    inputs = state.get("inputs", {}) or {}
    res = await SocialProducerAgent().run(
        AgentContext(
            state=dict(state),
            extra={
                "platforms": inputs.get("platforms", ["instagram", "tiktok"]),
                "post_count": inputs.get("post_count", 9),
                "story_count": inputs.get("story_count", 3),
            },
        )
    )
    summary = ""
    if res.ok:
        skill_res = res.skill_results[0] if res.skill_results else None
        counts = (skill_res.outputs.get("counts") if skill_res else {}) or {}
        summary = f"feed={counts.get('feed', 0)} story={counts.get('story', 0)}"
    return {
        **res.patch,
        "steps": [
            _step(
                "build_social",
                "social_producer",
                "build_social_pack",
                res.ok,
                started,
                summary,
                res.artifact_ids,
            )
        ],
        "errors": [] if res.ok else [{"stage": "social", "error": res.error}],
    }


@traced_node("critique_social")
async def _critic_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    social_pack = (state.get("output") or {}).get("social_pack") or {}
    visuals = state.get("visuals") or []
    feed_count = len([v for v in visuals if v.get("purpose") == "social:feed"])
    story_count = len([v for v in visuals if v.get("purpose") == "social:story"])
    # Critic sees the plan + visual counts, not the rendered pixels.
    candidate = {
        "design_system": state.get("design_system", {}),
        "strategy": state.get("strategy", {}),
        "captions": social_pack.get("captions", []),
        "hashtags": social_pack.get("hashtags", {}),
        "bios": social_pack.get("bios", {}),
        "cadence": social_pack.get("cadence", []),
        "counts": {"feed": feed_count, "story": story_count},
    }
    res = await CriticAgent().run(
        AgentContext(
            state=dict(state),
            extra={"target": "social", "candidate": candidate},
        )
    )
    iters = dict(state.get("iterations", {}))
    iters["critic_social"] = iters.get("critic_social", 0) + 1
    return {
        **res.patch,
        "iterations": iters,
        "steps": [_step("critique_social", "critic", "critique_output", res.ok, started)],
    }


def _route_after_critic(state: HelixState) -> str:
    critiques = state.get("critiques", [])
    if not critiques:
        return "finalize"
    last = critiques[-1]
    verdict = last.get("verdict", "accept")
    iters = state.get("iterations", {}).get("critic_social", 0)
    if verdict == "revise" and iters <= MAX_REVISIONS:
        return "revise_social"
    return "finalize"


@traced_node("finalize")
async def _finalize_node(state: HelixState) -> dict[str, Any]:
    social_pack = (state.get("output") or {}).get("social_pack") or {}
    visuals = state.get("visuals") or []
    output = dict(state.get("output", {}))
    output["social_summary"] = {
        "feed_count": len([v for v in visuals if v.get("purpose") == "social:feed"]),
        "story_count": len([v for v in visuals if v.get("purpose") == "social:story"]),
        "caption_count": len(social_pack.get("captions") or []),
        "cadence_days": len(social_pack.get("cadence") or []),
        "platforms": list((state.get("inputs") or {}).get("platforms", ["instagram", "tiktok"])),
    }
    return {"output": output}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph():
    g = StateGraph(HelixState)
    g.add_node("orchestrate", _orchestrator_node)
    g.add_node("load_prior", _load_prior_node)
    g.add_node("build_social", _social_producer_node)
    g.add_node("revise_social", _social_producer_node)
    g.add_node("critique", _critic_node)
    g.add_node("finalize", _finalize_node)

    g.add_edge(START, "orchestrate")
    g.add_edge("orchestrate", "load_prior")
    g.add_edge("load_prior", "build_social")
    g.add_edge("build_social", "critique")
    g.add_edge("revise_social", "critique")
    g.add_conditional_edges(
        "critique",
        _route_after_critic,
        {"revise_social": "revise_social", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)
    return g.compile()


_GRAPH = _build_graph()


async def execute(state: HelixState) -> HelixState:
    """Run the compiled graph and return the final state dict."""
    final = await _GRAPH.ainvoke(state)
    return final  # type: ignore[return-value]


register_workflow(SLICE_NAME, execute)
