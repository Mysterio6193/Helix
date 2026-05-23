"""MCP-compatible tool discovery + execution endpoints.

Exposes Helix's tool registry in a Model Context Protocol (MCP) shape so
external agents (Claude Desktop, Cursor, custom clients) can discover and
invoke our tools without learning a Helix-specific API.

All endpoints require authentication via the standard Helix session
cookie. The server version, protocol version, and human description are
sourced from settings so this stays in sync with the deployment without
code changes.

Routes
------
GET  /api/v1/mcp/info                  — server metadata
GET  /api/v1/mcp/tools                 — list tools with JSON schemas
POST /api/v1/mcp/tools/{name}/call     — invoke a tool
GET  /api/v1/mcp/models                — convenience: list chat/image/video catalog
"""
from __future__ import annotations

import inspect
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from helix.core.config import settings
from helix.core.logging import get_logger
from helix.core.sessions import require_user
from helix.llm import MODEL_CATALOG
from helix.models.organization import User
from helix.tools.base import Tool
from helix.tools.registry import get_tool, list_tools

router = APIRouter(prefix="/mcp", tags=["mcp"])
log = get_logger(__name__)


_MCP_PROTOCOL_VERSION = "2024-11-05"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class McpInfo(BaseModel):
    name: str
    version: str
    protocol_version: str
    capabilities: dict[str, bool]
    description: str


class McpToolSpec(BaseModel):
    name: str
    description: str
    inputSchema: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class McpToolList(BaseModel):
    tools: list[McpToolSpec]


class McpCallRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None


class McpCallResult(BaseModel):
    isError: bool
    content: list[dict[str, Any]]
    cost_usd: float | None = None
    latency_ms: int | None = None
    model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class McpModelEntry(BaseModel):
    id: str
    provider: str
    capability: str
    display_name: str
    tier: str
    available: bool


# ---------------------------------------------------------------------------
# Schema synthesis from tool signatures
# ---------------------------------------------------------------------------
_PY_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    bytes: "string",  # base64-encoded
}


def _annotation_to_jsonschema(ann: Any) -> dict[str, Any]:
    """Best-effort Python annotation → JSON schema fragment."""
    if ann is inspect.Parameter.empty or ann is None:
        return {"type": "string"}
    origin = getattr(ann, "__origin__", None)
    if origin is None:
        for py, js in _PY_TO_JSON.items():
            if ann is py:
                return {"type": js}
        return {"type": "string"}
    args = getattr(ann, "__args__", ())
    non_none = [a for a in args if a is not type(None)]
    if origin is list:
        item = non_none[0] if non_none else str
        return {"type": "array", "items": _annotation_to_jsonschema(item)}
    if origin is dict:
        return {"type": "object", "additionalProperties": True}
    if len(non_none) == 1:
        return _annotation_to_jsonschema(non_none[0])
    return {"type": "string"}


def _tool_to_schema(tool: Tool) -> McpToolSpec:
    try:
        sig = inspect.signature(tool._call)
    except (TypeError, ValueError):
        sig = None

    properties: dict[str, Any] = {}
    required: list[str] = []

    if sig:
        for pname, param in sig.parameters.items():
            if pname in ("self", "kwargs", "args"):
                continue
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            schema = _annotation_to_jsonschema(param.annotation)
            properties[pname] = schema
            if param.default is inspect.Parameter.empty:
                required.append(pname)

    return McpToolSpec(
        name=tool.name,
        description=tool.description or f"Helix tool: {tool.name}",
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": True,
        },
        metadata={
            "backend": tool.backend,
            "oauth_scopes": list(tool.oauth_scopes),
        },
    )


# ---------------------------------------------------------------------------
# Routes — all require an authenticated session.
# ---------------------------------------------------------------------------
@router.get("/info", response_model=McpInfo)
async def info(user: User = Depends(require_user)) -> McpInfo:
    return McpInfo(
        name="helix",
        version=settings.version,
        protocol_version=_MCP_PROTOCOL_VERSION,
        capabilities={"tools": True, "resources": False, "prompts": False},
        description="Helix creative OS — tool gateway for external agents.",
    )


@router.get("/tools", response_model=McpToolList)
async def list_mcp_tools(user: User = Depends(require_user)) -> McpToolList:
    tools = [_tool_to_schema(t) for t in list_tools()]
    tools.sort(key=lambda t: t.name)
    return McpToolList(tools=tools)


@router.post("/tools/{name}/call", response_model=McpCallResult)
async def call_mcp_tool(
    name: str,
    payload: McpCallRequest,
    user: User = Depends(require_user),
) -> McpCallResult:
    tool = get_tool(name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"unknown tool: {name}")

    log.info(
        "mcp.tool_call",
        tool=name,
        args=list(payload.arguments.keys()),
        user_id=str(user.id),
    )

    # Sessionless tools only — tools that need a DB session are gated.
    if "session" in payload.arguments:
        raise HTTPException(
            status_code=400,
            detail="session arg not supported via MCP — call this tool through the workflow runtime instead.",
        )

    result = await tool.call(trace_id=payload.trace_id, **payload.arguments)

    content: list[dict[str, Any]] = []
    if result.ok:
        content.append({"type": "json", "data": result.data})
    else:
        content.append({"type": "text", "text": result.error or "tool failed"})

    return McpCallResult(
        isError=not result.ok,
        content=content,
        cost_usd=result.cost_usd,
        latency_ms=result.latency_ms,
        model=result.model,
        metadata=result.metadata or {},
    )


@router.get("/models", response_model=list[McpModelEntry])
async def list_mcp_models(user: User = Depends(require_user)) -> list[McpModelEntry]:
    """Expose the LLM catalog so MCP clients can pick models too."""
    from helix.llm.catalog import _is_available

    return [
        McpModelEntry(
            id=spec.id,
            provider=spec.provider,
            capability=spec.capability,
            display_name=spec.display_name,
            tier=spec.tier,
            available=_is_available(spec),
        )
        for spec in MODEL_CATALOG.values()
    ]
