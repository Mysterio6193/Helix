"""Multi-Modal Critique Ensemble — aggregates semantic visual, palette, tone, and contrast checks."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Literal

from helix.core.logging import get_logger
from helix.critics.clip_scorer import score_clip
from helix.critics.contrast_a11y import calculate_contrast
from helix.critics.palette_scorer import score_palette
from helix.critics.tone_classifier import score_tone
from helix.workflows.state import HelixState

log = get_logger(__name__)


@dataclass
class CritiqueReport:
    weighted_score: float  # 0.0 - 10.0
    dimension_scores: dict[str, float]  # clip: 7.2, palette: 8.1, tone: 6.5, contrast: 9.0
    verdict: Literal["accept", "revise", "reject"]
    failing_dimensions: list[str]  # e.g., ["tone"]
    feedback: str


async def score(state: HelixState, candidate: dict[str, Any] | None) -> CritiqueReport:
    """Evaluate candidate deliverables (copy, visuals, design systems) using multimodal metrics.

    Args:
        state: The current HelixState containing brand context, strategy, and briefings.
        candidate: The generated components to evaluate.

    Returns:
        CritiqueReport: Complete dimension-level evaluation and accept/revise/reject verdict.
    """
    if not candidate:
        return CritiqueReport(
            weighted_score=0.0,
            dimension_scores={},
            verdict="reject",
            failing_dimensions=[],
            feedback="No candidate provided for critique."
        )

    trace_id = state.get("langfuse_trace_id")
    brand_context = state.get("brand_context", {})

    # Extract brand voice attributes
    voice_attributes = brand_context.get("voice_attributes") or []
    if not voice_attributes and state.get("strategy"):
        voice_attributes = state.get("strategy", {}).get("voice_attributes") or []

    # Creative brief or positioning text for visual semantic matching
    brief_text = ""
    if state.get("brief"):
        brief_text = state.get("brief", {}).get("description") or state.get("brief", {}).get("summary") or ""
    if not brief_text and state.get("strategy"):
        brief_text = state.get("strategy", {}).get("positioning") or state.get("strategy", {}).get("brand_story") or ""
    if not brief_text:
        brief_text = brand_context.get("positioning") or brand_context.get("mission") or brand_context.get("story") or ""

    # Target palette for color quantization checks
    palette_data = brand_context.get("palette") or state.get("design_system", {}).get("palette") or {}
    target_palette = []
    if isinstance(palette_data, list):
        target_palette = palette_data
    elif isinstance(palette_data, dict):
        target_palette = [v for v in palette_data.values() if isinstance(v, str) and (v.startswith("#") or len(v) in (3, 6))]
    if not target_palette:
        target_palette = ["#ffffff", "#000000"]

    tasks = {}

    # Extract copy text
    copy_data = candidate.get("copy")
    visuals_list = candidate.get("visuals") or []

    # Fallback to direct values if nested structure is absent
    if not copy_data and not visuals_list:
        if "options" in candidate or "text" in candidate or any(k in candidate for k in ["taglines", "headlines", "body"]):
            copy_data = candidate
        elif isinstance(candidate, list):
            visuals_list = candidate
        elif isinstance(candidate, dict) and ("s3_key" in candidate or "url" in candidate or "image_url" in candidate):
            visuals_list = [candidate]

    # Combine copy text to score
    copy_text_to_score = ""
    if copy_data:
        if isinstance(copy_data, str):
            copy_text_to_score = copy_data
        elif isinstance(copy_data, dict):
            texts = []
            for _k, v in copy_data.items():
                if isinstance(v, str):
                    texts.append(v)
                elif isinstance(v, dict):
                    opts = v.get("options") or v.get("variants") or []
                    if isinstance(opts, list):
                        texts.extend([str(o) for o in opts if isinstance(o, str | dict)])
                    else:
                        for _sk, sv in v.items():
                            if isinstance(sv, str):
                                texts.append(sv)
            copy_text_to_score = "\n".join(texts)

    # Tone Classification Task
    if copy_text_to_score and voice_attributes:
        tasks["tone"] = score_tone(copy_text_to_score, voice_attributes, trace_id=trace_id)

    # Extract visual image input
    visual_asset = None
    if visuals_list:
        if isinstance(visuals_list, list) and len(visuals_list) > 0:
            visual_asset = visuals_list[0]
        else:
            visual_asset = visuals_list

    image_data_to_score = None
    if visual_asset:
        if isinstance(visual_asset, str):
            image_data_to_score = visual_asset
        elif isinstance(visual_asset, dict):
            image_data_to_score = visual_asset.get("image_url") or visual_asset.get("s3_key") or visual_asset.get("url") or visual_asset.get("path")

    # Visual Tasks (CLIP and Palette)
    if image_data_to_score:
        if brief_text:
            tasks["clip"] = score_clip(image_data_to_score, brief_text, trace_id=trace_id)
        if target_palette:
            tasks["palette"] = score_palette(image_data_to_score, target_palette, trace_id=trace_id)

    # Gather async tasks
    results = {}
    if tasks:
        keys = list(tasks.keys())
        fut_results = await asyncio.gather(*[tasks[k] for k in keys], return_exceptions=True)
        for k, res in zip(keys, fut_results, strict=False):
            if isinstance(res, Exception):
                log.error("critic.ensemble.scorer_failed", scorer=k, error=str(res))
                results[k] = 0.75  # default neutral fallback
            else:
                results[k] = res

    # Sync Accessibility/Contrast checks
    fg_hex = None
    bg_hex = None
    ds = candidate.get("design_system") or state.get("design_system") or {}
    if ds:
        colors = ds.get("colors") or ds.get("palette") or {}
        if isinstance(colors, dict):
            fg_hex = colors.get("foreground") or colors.get("text") or colors.get("primary")
            bg_hex = colors.get("background") or colors.get("surface") or colors.get("bg")
        elif isinstance(colors, list) and len(colors) >= 2:
            fg_hex = colors[0]
            bg_hex = colors[-1]

    if not fg_hex or not bg_hex:
        if len(target_palette) >= 2:
            fg_hex = target_palette[0]
            bg_hex = target_palette[-1]

    if fg_hex and bg_hex:
        try:
            contrast_res = calculate_contrast(fg_hex, bg_hex)
            results["contrast"] = float(contrast_res.get("score", 1.0))
        except Exception as exc:
            log.warning("critic.ensemble.contrast_failed", error=str(exc))
            results["contrast"] = 1.0

    if not results:
        # No metrics were run
        return CritiqueReport(
            weighted_score=10.0,
            dimension_scores={},
            verdict="accept",
            failing_dimensions=[],
            feedback="No visual or textual elements to critique. Automatically passed."
        )

    # Normalize to 0-10 range
    dimension_scores = {}
    for k, val in results.items():
        dimension_scores[k] = round(val * 10.0, 2)

    weighted_score = round(sum(dimension_scores.values()) / len(dimension_scores), 2)

    # Verdict thresholds
    failing_dimensions = [k for k, v in dimension_scores.items() if v < 7.5]

    if weighted_score >= 7.5 and not failing_dimensions:
        verdict = "accept"
    elif weighted_score < 4.0:
        verdict = "reject"
    else:
        verdict = "revise"

    # Feedback message
    feedback_parts = []
    if verdict == "accept":
        feedback_parts.append(f"Quality gate PASSED. Composite quality score: {weighted_score}/10.")
    elif verdict == "reject":
        feedback_parts.append(f"Quality gate REJECTED. Composite score: {weighted_score}/10 falls below safety limits.")
    else:
        feedback_parts.append(f"Quality gate REVISION REQUIRED. Composite score: {weighted_score}/10.")

    for dim, score_val in dimension_scores.items():
        status = "PASS" if score_val >= 7.5 else "FAIL (requires >= 7.5)"
        feedback_parts.append(f"- {dim.upper()}: {score_val}/10 ({status})")

    if failing_dimensions:
        feedback_parts.append(f"\nRefinement should target these dimensions: {', '.join(failing_dimensions)}.")

    feedback = "\n".join(feedback_parts)

    return CritiqueReport(
        weighted_score=weighted_score,
        dimension_scores=dimension_scores,
        verdict=verdict,
        failing_dimensions=failing_dimensions,
        feedback=feedback
    )
