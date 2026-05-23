"""LLM-powered brand tone and copywriting style critic."""
from __future__ import annotations

import json
from typing import Any

from helix.core.logging import get_logger
from helix.tools.registry import get_tool

log = get_logger(__name__)


async def score_tone(
    text: str,
    voice_attributes: list[str],
    trace_id: str | None = None,
) -> float:
    """Score the alignment of generated text against target voice attributes.

    Returns:
        float: Bounded tone score between 0.0 and 1.0.
    """
    if not text:
        return 0.0
    if not voice_attributes:
        return 1.0

    llm_tool = get_tool("openai_chat")
    if not llm_tool:
        log.warning("tone_classifier.no_llm_tool_found")
        return 0.8  # Safe default

    system_prompt = (
        "You are an expert brand editor and copy classifier. Your task is to evaluate "
        "whether the provided text copy matches the target brand voice attributes.\n"
        "Assess grammar, flow, emotional resonance, vocabulary, and vocabulary constraints.\n"
        "Respond with a single JSON object containing 'score' (a float from 0.0 to 1.0) "
        "and a concise 'reasoning' explanation (1-2 sentences)."
    )

    prompt = (
        f"Target Voice Attributes: {', '.join(voice_attributes)}\n\n"
        f"Generated Copy:\n\"\"\"\n{text}\n\"\"\"\n\n"
        f"Assess how well the copy matches the brand's voice and tone."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    try:
        res = await llm_tool.call(
            trace_id=trace_id,
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.1,
            json_mode=True,
        )
        if res.ok and res.data:
            data = res.data if isinstance(res.data, dict) else json.loads(str(res.data))
            score_val = float(data.get("score", 0.8))
            return max(0.0, min(1.0, score_val))
    except Exception as exc:
        log.exception("tone_classifier.failed", error=str(exc))

    return 0.8  # Fallback default
