"""Tool registry: in-memory map of name -> Tool instance, populated by bootstrap."""
from __future__ import annotations

from helix.tools.base import Tool

_REGISTRY: dict[str, Tool] = {}


def register_tool(tool: Tool) -> None:
    _REGISTRY[tool.name] = tool


def get_tool(name: str) -> Tool | None:
    return _REGISTRY.get(name)


def list_tools() -> list[Tool]:
    return list(_REGISTRY.values())


def clear_registry() -> None:
    """Test hook."""
    _REGISTRY.clear()
