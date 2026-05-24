"""Slice 6: Boardroom Suite.

Graph:
   boardroom_debate -> END

Runs the multi-agent council debate to autonomously resolve marketing events.
"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from helix.agents.base import AgentContext
from helix.agents.executive_council import ExecutiveCouncilAgent
from helix.core.logging import get_logger
from helix.core.observability import traced_node
from helix.workflows.runner import register_workflow
from helix.workflows.state import HelixState

log = get_logger(__name__)

SLICE_NAME = "executive_council"


def _step(
    name: str,
    agent: str,
    skill: str | None,
    ok: bool,
    started: float,
    summary: str = "",
) -> dict[str, Any]:
    return {
        "step": name,
        "agent": agent,
        "skill": skill,
        "started_at": started,
        "ended_at": time.time(),
        "status": "ok" if ok else "error",
        "output_summary": summary,
    }


@traced_node("boardroom_debate")
async def _boardroom_node(state: HelixState) -> dict[str, Any]:
    started = time.time()
    res = await ExecutiveCouncilAgent().run(AgentContext(state=dict(state)))
    summary = (
        (res.patch.get("boardroom_decision") or {}).get("summary")
        if res.ok
        else res.error or "Debate failed"
    )
    return {
        **res.patch,
        "steps": [
            _step("boardroom_debate", "executive_council", None, res.ok, started, summary)
        ],
        "errors": [] if res.ok else [{"stage": "boardroom", "error": res.error}],
    }


def _build_graph():
    g = StateGraph(HelixState)
    g.add_node("boardroom_debate", _boardroom_node)
    g.add_edge(START, "boardroom_debate")
    g.add_edge("boardroom_debate", END)
    return g.compile()


_GRAPH = _build_graph()


async def execute(state: HelixState) -> HelixState:
    """Run compiled boardroom graph and return final state dict."""
    final = await _GRAPH.ainvoke(state)
    return final  # type: ignore[return-value]


register_workflow(SLICE_NAME, execute)
