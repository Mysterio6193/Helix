"""Langfuse client, lazy-initialized. No-op if keys absent."""
from __future__ import annotations

from typing import Any

from helix.core.config import settings
from helix.core.logging import get_logger

logger = get_logger("langfuse")

_client: Any | None = None
_initialized = False


def get_langfuse() -> Any | None:
    """Return Langfuse client or None when not configured."""
    global _client, _initialized
    if _initialized:
        return _client
    _initialized = True
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        logger.info("langfuse_disabled", reason="missing-keys")
        return None
    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("langfuse_init_failed", error=str(exc))
        _client = None
    return _client


def trace(name: str, **metadata: Any) -> Any | None:
    """Create a trace if Langfuse is configured."""
    client = get_langfuse()
    if client is None:
        return None
    try:
        return client.trace(name=name, metadata=metadata)
    except Exception:  # pragma: no cover
        return None
