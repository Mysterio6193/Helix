"""CLIP-style image-text similarity scorer using multimodal vision-LLM."""
from __future__ import annotations

import base64
from typing import Any

from helix.core.logging import get_logger
from helix.tools.registry import get_tool

log = get_logger(__name__)


async def score_clip(
    image_data: bytes | str,
    brief_text: str,
    trace_id: str | None = None,
) -> float:
    """Score semantic alignment between a generated image and a brand brief.

    Args:
        image_data: Image bytes or public URL or base64 data URL.
        brief_text: Brand strategy or creative brief.
        trace_id: Optional Langfuse trace ID.

    Returns:
        float: Alignment score between 0.0 and 1.0.
    """
    llm_tool = get_tool("openai_chat")
    if not llm_tool:
        log.warning("clip_scorer.no_llm_tool_found")
        return 0.75  # Safe default

    # If it is raw bytes, convert to base64 data URL
    if isinstance(image_data, bytes):
        b64 = base64.b64encode(image_data).decode("utf-8")
        image_url = f"data:image/png;base64,{b64}"
    elif isinstance(image_data, str) and not image_data.startswith("http") and not image_data.startswith("data:"):
        # Assume it might be raw base64 or an S3 key. If it looks like base64, wrap it.
        if len(image_data) > 1000:
            image_url = f"data:image/png;base64,{image_data}"
        else:
            # Let's try downloading from S3 using S3StorageTool if available
            s3_tool = get_tool("s3_storage")
            if s3_tool:
                try:
                    res = await s3_tool.call(trace_id=trace_id, action="get_url", key=image_data)
                    if res.ok and isinstance(res.data, dict):
                        image_url = res.data.get("url", "")
                    else:
                        image_url = image_data
                except Exception:
                    image_url = image_data
            else:
                image_url = image_data
    else:
        image_url = image_data

    system_prompt = (
        "You are an expert multi-modal brand critic. Your task is to score the alignment "
        "between a generated visual asset and the creative brand brief/positioning.\n"
        "Analyze color, theme, imagery, style, and general emotional resonance.\n"
        "Respond with a single JSON object containing 'score' (a float from 0.0 to 1.0) "
        "and a concise 'reasoning' explanation (1-2 sentences)."
    )

    prompt = f"Brand Brief / Positioning:\n{brief_text}\n\nAssess how well the attached image aligns with this brief."

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        },
    ]

    try:
        res = await llm_tool.call(
            trace_id=trace_id,
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.2,
            json_mode=True,
        )
        if res.ok and res.data:
            import json
            # Handle if data is already a dict or a string
            data = res.data if isinstance(res.data, dict) else json.loads(str(res.data))
            score_val = float(data.get("score", 0.75))
            # Clamp between 0 and 1
            return max(0.0, min(1.0, score_val))
    except Exception as exc:
        log.exception("clip_scorer.failed", error=str(exc))

    return 0.75  # Fallback default
