"""Observability decorators — auto-instrument nodes, tools, and skills with Langfuse spans.

All decorators are safe no-ops when Langfuse is not configured.  Never crash
on observability failures — always swallow and log.
"""
from __future__ import annotations

import functools
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from helix.core.langfuse_client import get_langfuse
from helix.core.logging import get_logger

log = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Low-level span context manager
# ---------------------------------------------------------------------------

@asynccontextmanager
async def span_ctx(
    trace_id: str | None,
    name: str,
    *,
    input_data: Any = None,
    metadata: dict[str, Any] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Open a Langfuse span.  Yields a mutable dict where callers can set
    ``output``, ``status_message``, ``level``, or extra ``metadata``.

    Safe no-op when Langfuse is absent or ``trace_id`` is None.
    """
    ctx: dict[str, Any] = {"span": None}
    lf = get_langfuse()
    if lf and trace_id:
        try:
            span = lf.span(
                trace_id=trace_id,
                name=name,
                input=input_data,
                metadata=metadata or {},
            )
            ctx["span"] = span
        except Exception:
            log.debug("observability.span_open_failed", name=name, exc_info=True)

    started = time.perf_counter()
    try:
        yield ctx
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000
        span = ctx.get("span")
        if span:
            try:
                span.end(
                    output=ctx.get("output"),
                    status_message=ctx.get("status_message"),
                    level=ctx.get("level", "DEFAULT"),
                    metadata={
                        **(metadata or {}),
                        "duration_ms": round(elapsed_ms, 2),
                        **(ctx.get("metadata") or {}),
                    },
                )
            except Exception:
                log.debug("observability.span_close_failed", name=name, exc_info=True)


# ---------------------------------------------------------------------------
# traced_node — decorator for LangGraph node functions
# ---------------------------------------------------------------------------

def traced_node(name: str) -> Callable:
    """Wrap an async LangGraph node function with a Langfuse span.

    The decorated function must accept ``state: HelixState`` as its first arg
    and return a dict patch.  The ``langfuse_trace_id`` is read from state.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(state: dict, *args: Any, **kwargs: Any) -> Any:
            trace_id = state.get("langfuse_trace_id") if isinstance(state, dict) else None
            input_keys = list(state.keys()) if isinstance(state, dict) else []

            async with span_ctx(
                trace_id,
                f"node:{name}",
                input_data={"state_keys": input_keys[:20]},
                metadata={"node": name},
            ) as ctx:
                result = await fn(state, *args, **kwargs)
                if isinstance(result, dict):
                    ctx["output"] = {
                        "patch_keys": list(result.keys())[:20],
                        "has_errors": bool(result.get("errors")),
                    }
                return result

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# traced_tool — decorator for Tool._call methods
# ---------------------------------------------------------------------------

def traced_tool() -> Callable:
    """Wrap the ``Tool.call()`` method to record cost, latency, and model."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(self: Any, *, trace_id: str | None = None, **kwargs: Any) -> Any:
            async with span_ctx(
                trace_id,
                f"tool:{getattr(self, 'name', 'unknown')}",
                input_data={k: str(v)[:200] for k, v in kwargs.items()},
                metadata={"tool": getattr(self, "name", "unknown")},
            ) as ctx:
                result = await fn(self, **kwargs)

                if result and hasattr(result, "ok"):
                    ctx["output"] = {
                        "ok": result.ok,
                        "cost_usd": getattr(result, "cost_usd", None),
                        "latency_ms": getattr(result, "latency_ms", None),
                        "model": getattr(result, "model", None),
                    }
                    if not result.ok:
                        ctx["level"] = "WARNING"
                        ctx["status_message"] = getattr(result, "error", "")

                    # Emit Langfuse generation if model is present
                    lf = get_langfuse()
                    if lf and trace_id and getattr(result, "model", None):
                        try:
                            meta = getattr(result, "metadata", {}) or {}
                            lf.generation(
                                trace_id=trace_id,
                                name=f"gen:{getattr(self, 'name', 'unknown')}",
                                model=result.model,
                                usage={
                                    "input": meta.get("prompt_tokens"),
                                    "output": meta.get("completion_tokens"),
                                },
                                metadata={
                                    "cost_usd": getattr(result, "cost_usd", None),
                                },
                            )
                        except Exception:
                            log.debug("observability.generation_failed", exc_info=True)

                return result

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# traced_skill — decorator for skill handler invocations
# ---------------------------------------------------------------------------

def traced_skill(name: str) -> Callable:
    """Wrap a skill handler to record success, cost, and token counts."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try to extract trace_id from SkillContext
            trace_id = None
            for arg in args:
                if hasattr(arg, "state") and isinstance(arg.state, dict):
                    trace_id = arg.state.get("langfuse_trace_id")
                    break

            async with span_ctx(
                trace_id,
                f"skill:{name}",
                metadata={"skill": name},
            ) as ctx:
                result = await fn(*args, **kwargs)

                if result and hasattr(result, "ok"):
                    ctx["output"] = {
                        "ok": result.ok,
                        "cost_usd": getattr(result, "cost_usd", None),
                        "artifact_count": len(getattr(result, "artifacts", []) or []),
                    }
                    if not result.ok:
                        ctx["level"] = "WARNING"
                        ctx["status_message"] = getattr(result, "error", "")

                return result

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Utility: score a trace
# ---------------------------------------------------------------------------

def score_trace(
    trace_id: str | None,
    name: str,
    value: float,
    *,
    comment: str | None = None,
) -> None:
    """Record a Langfuse score.  Safe no-op when Langfuse absent."""
    if not trace_id:
        return
    lf = get_langfuse()
    if not lf:
        return
    try:
        lf.score(trace_id=trace_id, name=name, value=value, comment=comment)
    except Exception:
        log.debug("observability.score_failed", name=name, exc_info=True)
