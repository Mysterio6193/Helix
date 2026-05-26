"""Embedding generation. Requires a configured OpenAI API key — fails fast otherwise.

Previous versions returned a deterministic hash-based pseudo-embedding when no key
was configured. That silently produced semantically meaningless vectors that
poisoned downstream similarity search. We now require a real provider.
"""
from __future__ import annotations

from collections.abc import Iterable

from helix.core.config import get_settings
from helix.core.logging import get_logger

log = get_logger(__name__)

EMBED_DIM = 1536


class EmbeddingProviderError(RuntimeError):
    """Raised when no embedding provider is configured or the call fails."""


async def embed(text: str) -> list[float]:
    """Return a single 1536-dim embedding from OpenAI text-embedding-3-small.

    Raises EmbeddingProviderError if the OpenAI key is missing or the call fails.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise EmbeddingProviderError(
            "OPENAI_API_KEY is not configured. Set it to enable embeddings."
        )
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(model="text-embedding-3-small", input=text)
        return list(resp.data[0].embedding)
    except Exception as exc:
        log.exception("embedding_request_failed")
        raise EmbeddingProviderError(f"embedding request failed: {exc}") from exc


async def embed_batch(texts: Iterable[str]) -> list[list[float]]:
    return [await embed(t) for t in texts]
