"""Embedding generation with graceful fallback when no API key configured."""
from __future__ import annotations

import hashlib
from collections.abc import Iterable

from helix.core.config import get_settings

EMBED_DIM = 1536


def _deterministic_embedding(text: str, dim: int = EMBED_DIM) -> list[float]:
    """Hash-based pseudo-embedding for offline/dev use. Stable per input."""
    rng_seed = hashlib.sha256(text.encode("utf-8")).digest()
    out: list[float] = []
    i = 0
    while len(out) < dim:
        chunk = rng_seed if i == 0 else hashlib.sha256(rng_seed + i.to_bytes(4, "big")).digest()
        for b in chunk:
            out.append((b - 128) / 128.0)
            if len(out) >= dim:
                break
        i += 1
    # L2-ish normalize for cosine distance stability
    norm = sum(v * v for v in out) ** 0.5 or 1.0
    return [v / norm for v in out]


async def embed(text: str) -> list[float]:
    """Return a single 1536-dim embedding."""
    settings = get_settings()
    if not settings.openai_api_key:
        return _deterministic_embedding(text)
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(model="text-embedding-3-small", input=text)
        return list(resp.data[0].embedding)
    except Exception:
        return _deterministic_embedding(text)


async def embed_batch(texts: Iterable[str]) -> list[list[float]]:
    return [await embed(t) for t in texts]
