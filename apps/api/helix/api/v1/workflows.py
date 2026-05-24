"""Workflows API: introspection over Helix execution plans.

All endpoints require authentication. The set of available workflow plans is
discovered dynamically at request time so newly added plans appear without a
hardcoded public list. The fallback topology is a generic linear plan that's
always safe to render when plan introspection is unavailable.
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from helix.core.sessions import require_user
from helix.models.organization import User

router = APIRouter(prefix="/workflows", tags=["workflows"])

_SLICES_PACKAGE = "helix.workflows.slices"


def _discover_slices() -> dict[str, str]:
    """Return {workflow_name: fully_qualified_module}. Runs at request time
    so newly added slice files appear without restart."""
    try:
        pkg = importlib.import_module(_SLICES_PACKAGE)
    except ImportError:
        return {}
    out: dict[str, str] = {}
    for info in pkgutil.iter_modules(pkg.__path__):
        if info.ispkg or info.name.startswith("_"):
            continue
        out[info.name] = f"{_SLICES_PACKAGE}.{info.name}"
    return out


def _generic_fallback() -> dict[str, list[dict[str, Any]]]:
    """Generic topology used when execution-plan introspection is unavailable."""
    nodes = [
        {"id": "__start__", "label": "Start"},
        {"id": "orchestrate", "label": "Orchestrate"},
        {"id": "generate", "label": "Generate"},
        {"id": "critique", "label": "Critique Ensemble"},
        {"id": "revise", "label": "Revise"},
        {"id": "finalize", "label": "Finalize & Save"},
        {"id": "__end__", "label": "End"},
    ]
    edges = [
        {"id": "start->orch", "source": "__start__", "target": "orchestrate"},
        {"id": "orch->gen", "source": "orchestrate", "target": "generate"},
        {"id": "gen->critique", "source": "generate", "target": "critique"},
        {"id": "critique->revise", "source": "critique", "target": "revise", "label": "Needs Revision"},
        {"id": "revise->critique", "source": "revise", "target": "critique"},
        {"id": "critique->finalize", "source": "critique", "target": "finalize", "label": "Accept"},
        {"id": "finalize->end", "source": "finalize", "target": "__end__"},
    ]
    return {"nodes": nodes, "edges": edges}


@router.get("")
async def list_workflows(
    user: User = Depends(require_user),
) -> dict[str, Any]:
    """List the workflows available on this deployment."""
    slices = _discover_slices()
    return {
        "workflows": [
            {"name": name, "title": name.replace("_", " ").title()}
            for name, module in sorted(slices.items())
        ]
    }


@router.get("/{workflow_name}/graph")
async def get_workflow_graph(
    workflow_name: str,
    user: User = Depends(require_user),
) -> dict[str, list[dict[str, Any]]]:
    """Return visual nodes and edges for the compiled Helix workflow."""
    slices = _discover_slices()
    if workflow_name not in slices:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    try:
        mod = importlib.import_module(slices[workflow_name])
        graph = getattr(mod, "_GRAPH", None)
        if graph is None:
            return _generic_fallback()

        g = graph.get_graph()
        nodes: list[dict[str, Any]] = []
        for node_id, node in g.nodes.items():
            label = getattr(node, "name", str(node_id))
            if label.startswith("_"):
                label = label[1:]
            if label.endswith("_node"):
                label = label[:-5]
            label = label.replace("_", " ").title()
            nodes.append({"id": str(node_id), "label": label})

        edges: list[dict[str, Any]] = []
        for edge in g.edges:
            label = edge.conditional if hasattr(edge, "conditional") else None
            edges.append({
                "id": f"{edge.source}->{edge.target}",
                "source": str(edge.source),
                "target": str(edge.target),
                "label": label,
            })

        return {"nodes": nodes, "edges": edges}
    except Exception:
        return _generic_fallback()
