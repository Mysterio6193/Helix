"""Prometheus metrics — process counters and an HTTP middleware-free helper.

Designed so that `prometheus_client` is optional: when it isn't installed the
`/metrics` endpoint returns a plain-text snapshot of the in-process counters
instead of failing.

Counters are all created via small helpers so we can no-op cleanly when the
prometheus package is missing.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any

try:  # pragma: no cover - import guard
    from prometheus_client import (  # type: ignore
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    _PROM = True
    _REGISTRY = CollectorRegistry()
except Exception:  # noqa: BLE001
    _PROM = False
    _REGISTRY = None  # type: ignore[assignment]
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


# ---------------------------------------------------------------------------
# Fallback in-process counters (always present)
# ---------------------------------------------------------------------------
_LOCK = threading.Lock()
_COUNTERS: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)
_GAUGES: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)


def _label_key(labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not labels:
        return ()
    return tuple(sorted(labels.items()))


# ---------------------------------------------------------------------------
# Optional prometheus wrappers
# ---------------------------------------------------------------------------
_prom_counters: dict[str, Any] = {}
_prom_gauges: dict[str, Any] = {}
_prom_histograms: dict[str, Any] = {}


def _ensure_counter(name: str, description: str, labelnames: tuple[str, ...]) -> Any:
    if not _PROM:
        return None
    if name not in _prom_counters:
        _prom_counters[name] = Counter(name, description, labelnames=labelnames, registry=_REGISTRY)
    return _prom_counters[name]


def _ensure_gauge(name: str, description: str, labelnames: tuple[str, ...]) -> Any:
    if not _PROM:
        return None
    if name not in _prom_gauges:
        _prom_gauges[name] = Gauge(name, description, labelnames=labelnames, registry=_REGISTRY)
    return _prom_gauges[name]


def _ensure_histogram(name: str, description: str, labelnames: tuple[str, ...]) -> Any:
    if not _PROM:
        return None
    if name not in _prom_histograms:
        _prom_histograms[name] = Histogram(
            name, description, labelnames=labelnames, registry=_REGISTRY
        )
    return _prom_histograms[name]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def inc(name: str, description: str = "", labels: dict[str, str] | None = None, amount: float = 1.0) -> None:
    with _LOCK:
        _COUNTERS[name][_label_key(labels)] = _COUNTERS[name].get(_label_key(labels), 0.0) + amount
    c = _ensure_counter(name, description, tuple(sorted(labels.keys())) if labels else ())
    if c is not None:
        if labels:
            c.labels(**labels).inc(amount)
        else:
            c.inc(amount)


def set_gauge(name: str, value: float, description: str = "", labels: dict[str, str] | None = None) -> None:
    with _LOCK:
        _GAUGES[name][_label_key(labels)] = value
    g = _ensure_gauge(name, description, tuple(sorted(labels.keys())) if labels else ())
    if g is not None:
        if labels:
            g.labels(**labels).set(value)
        else:
            g.set(value)


def observe(name: str, value: float, description: str = "", labels: dict[str, str] | None = None) -> None:
    h = _ensure_histogram(name, description, tuple(sorted(labels.keys())) if labels else ())
    if h is not None:
        if labels:
            h.labels(**labels).observe(value)
        else:
            h.observe(value)


def metrics_response() -> tuple[bytes, str]:
    """Return (body, content_type) for the /metrics endpoint."""
    if _PROM and _REGISTRY is not None:
        return generate_latest(_REGISTRY), CONTENT_TYPE_LATEST

    # Plaintext fallback — Prometheus text format compatible.
    lines: list[str] = [f"# helix metrics fallback (prometheus_client not installed) {int(time.time())}"]
    with _LOCK:
        for name, by_labels in _COUNTERS.items():
            for label_tuple, value in by_labels.items():
                label_str = (
                    "{" + ",".join(f'{k}="{v}"' for k, v in label_tuple) + "}"
                    if label_tuple
                    else ""
                )
                lines.append(f"{name}{label_str} {value}")
        for name, by_labels in _GAUGES.items():
            for label_tuple, value in by_labels.items():
                label_str = (
                    "{" + ",".join(f'{k}="{v}"' for k, v in label_tuple) + "}"
                    if label_tuple
                    else ""
                )
                lines.append(f"{name}{label_str} {value}")
    return ("\n".join(lines) + "\n").encode("utf-8"), CONTENT_TYPE_LATEST
