"""Slice 3: Website Suite.

Graph:
   orchestrator -> load_prior -> web_builder -> critic -> (revise_web | finalize) -> END

The web_builder runs `build_restaurant_site` which internally:
  - generates section copy
  - renders TSX + Tailwind + config files
  - (optionally) creates a GitHub repo + Vercel deployment

The critic inspects the section copy + file tree summary. One revision allowed —
if the critic flags a copy regression the section generator re-runs; the file
renderer is deterministic once copy is in place.
"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from helix.agents.base import AgentContext
from helix.agents.critic import CriticAgent
from helix.agents.orchestrator import OrchestratorAgent
from helix.agents.web_builder import WebBuilderAgent
from helix.core.logging import get_logger
from helix.core.observability import traced_node
from helix.workflows.runner import register_workflow
from helix.workflows.state import HelixState

log = get_logger(__name__)


SLICE_NAME = "website_suite"
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


@traced_node("build_site")
async def _web_builder_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    inputs = state.get("inputs", {}) or {}
    res = await WebBuilderAgent().run(
        AgentContext(
            state=dict(state),
            extra={"deploy": bool(inputs.get("deploy", False))},
        )
    )
    summary = ""
    website = (res.patch.get("output") or {}).get("website") if res.ok else None
    if website:
        deploy_url = (website.get("deployment") or {}).get("url")
        summary = f"files={website.get('file_count', 0)} url={deploy_url or '—'}"
    return {
        **res.patch,
        "steps": [
            _step(
                "build_site",
                "web_builder",
                "build_restaurant_site",
                res.ok,
                started,
                summary,
                res.artifact_ids,
            )
        ],
        "errors": [] if res.ok else [{"stage": "website", "error": res.error}],
    }


@traced_node("critique_website")
async def _critic_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    website = (state.get("output") or {}).get("website") or {}
    # We hand the critic the section copy + file path list, not the rendered
    # source — the critic shouldn't be grading TSX, just copy + structure.
    candidate = {
        "design_system": state.get("design_system", {}),
        "strategy": state.get("strategy", {}),
        "sections": website.get("sections", {}),
        "file_paths": list((website.get("files") or {}).keys()),
        "deployment": website.get("deployment"),
    }
    res = await CriticAgent().run(
        AgentContext(
            state=dict(state),
            extra={"target": "website", "candidate": candidate},
        )
    )
    iters = dict(state.get("iterations", {}))
    iters["critic_website"] = iters.get("critic_website", 0) + 1
    return {
        **res.patch,
        "iterations": iters,
        "steps": [_step("critique_website", "critic", "critique_output", res.ok, started)],
    }


def _route_after_critic(state: HelixState) -> str:
    critiques = state.get("critiques", [])
    if not critiques:
        return "finalize"
    last = critiques[-1]
    verdict = last.get("verdict", "accept")
    iters = state.get("iterations", {}).get("critic_website", 0)
    if verdict == "revise" and iters <= MAX_REVISIONS:
        return "revise_web"
    return "finalize"


@traced_node("finalize")
async def _finalize_node(state: HelixState) -> dict[str, Any]:
    website = (state.get("output") or {}).get("website") or {}
    output = dict(state.get("output", {}))
    output["website_summary"] = {
        "slug": website.get("slug"),
        "file_count": website.get("file_count"),
        "deployment_url": (website.get("deployment") or {}).get("url"),
        "repo_url": (website.get("repo") or {}).get("url"),
    }
    return {"output": output}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph():
    g = StateGraph(HelixState)
    g.add_node("orchestrate", _orchestrator_node)
    g.add_node("load_prior", _load_prior_node)
    g.add_node("build_site", _web_builder_node)
    g.add_node("revise_web", _web_builder_node)
    g.add_node("critique", _critic_node)
    g.add_node("finalize", _finalize_node)

    g.add_edge(START, "orchestrate")
    g.add_edge("orchestrate", "load_prior")
    g.add_edge("load_prior", "build_site")
    g.add_edge("build_site", "critique")
    g.add_edge("revise_web", "critique")
    g.add_conditional_edges(
        "critique",
        _route_after_critic,
        {"revise_web": "revise_web", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)
    return g.compile()


_GRAPH = _build_graph()


async def execute(state: HelixState) -> HelixState:
    """Run the compiled graph and return the final state dict."""
    final = await _GRAPH.ainvoke(state)
    return final  # type: ignore[return-value]


register_workflow(SLICE_NAME, execute)
