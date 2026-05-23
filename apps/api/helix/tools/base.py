"""Base Tool contract — multi-backend execution (Hermes pattern)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from helix.core.logging import get_logger

log = get_logger("helix.tools.base")


@dataclass
class ToolResult:
    """Uniform return shape for every tool call."""

    ok: bool
    data: Any = None
    error: str | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Tool:
    """Subclass and implement `_call`. Backends: local, docker, remote API."""

    name: str = "tool"
    description: str = ""
    oauth_scopes: list[str] = []
    backend: str = "local"  # local | docker | remote

    async def call(self, *, trace_id: str | None = None, **kwargs: Any) -> ToolResult:
        from helix.core.observability import span_ctx

        started = time.perf_counter()
        async with span_ctx(
            trace_id,
            f"tool:{self.name}",
            input_data={k: str(v)[:200] for k, v in kwargs.items()},
            metadata={"tool": self.name, "backend": self.backend},
        ) as ctx:
            try:
                result = await self._call(**kwargs)
                if result.latency_ms is None:
                    result.latency_ms = int((time.perf_counter() - started) * 1000)
                ctx["output"] = {
                    "ok": result.ok,
                    "cost_usd": result.cost_usd,
                    "latency_ms": result.latency_ms,
                    "model": result.model,
                }
                if not result.ok:
                    ctx["level"] = "WARNING"
                    ctx["status_message"] = result.error
                return result
            except Exception as exc:  # noqa: BLE001 - we re-raise via ToolResult
                log.exception("tool.call_failed", tool=self.name, error=str(exc))
                ctx["level"] = "ERROR"
                ctx["status_message"] = str(exc)
                return ToolResult(
                    ok=False,
                    error=str(exc),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )

    async def _call(self, **kwargs: Any) -> ToolResult:  # pragma: no cover - abstract
        raise NotImplementedError(f"Tool '{self.name}' must implement _call")

    def estimate_cost(self, **kwargs: Any) -> float:
        return 0.0
