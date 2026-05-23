"""Deterministic WCAG 2.2 AA / AAA color contrast ratio calculator."""
from __future__ import annotations


def _parse_rgb(hex_str: str) -> tuple[float, float, float]:
    """Parse hex color (with or without #) to normalized RGB float tuple (0.0 - 1.0)."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return r, g, b


def _channel_luminance(c: float) -> float:
    """Calculate relative channel luminance according to W3C formula."""
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_str: str) -> float:
    """Calculate relative luminance (0.0 - 1.0) of a hex color."""
    r, g, b = _parse_rgb(hex_str)
    rl = _channel_luminance(r)
    gl = _channel_luminance(g)
    bl = _channel_luminance(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def calculate_contrast(fg_hex: str, bg_hex: str) -> dict[str, Any]:
    """Calculate WCAG 2.2 contrast ratio between foreground and background colors.

    Args:
        fg_hex: Foreground color hex string (e.g., "#ffffff").
        bg_hex: Background color hex string (e.g., "#000000").

    Returns:
        dict: containing:
            - ratio: actual contrast ratio (1.0 to 21.0)
            - aa_pass: boolean indicating normal text AA compliance (>= 4.5)
            - aaa_pass: boolean indicating normal text AAA compliance (>= 7.0)
            - score: normalized accessibility score from 0.0 to 1.0
    """
    try:
        l1 = _relative_luminance(fg_hex)
        l2 = _relative_luminance(bg_hex)
    except Exception:
        # Fallback if hex color format is bad
        return {"ratio": 1.0, "aa_pass": False, "aaa_pass": False, "score": 0.0}

    # Contrast ratio = (L1 + 0.05) / (L2 + 0.05) where L1 is lighter than L2
    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)

    aa_pass = ratio >= 4.5
    aaa_pass = ratio >= 7.0

    # Map ratio to a 0.0 - 1.0 score
    # A ratio of 4.5 is the minimum baseline (score = 0.5), 7.0+ gets 0.8+, 21.0 gets 1.0.
    if ratio < 3.0:
        score_val = (ratio - 1.0) / 4.0  # 1.0-3.0 maps to 0.0-0.5
    elif ratio < 4.5:
        score_val = 0.5 + (ratio - 3.0) / 3.0 * 0.2  # 3.0-4.5 maps to 0.5-0.7
    elif ratio < 7.0:
        score_val = 0.7 + (ratio - 4.5) / 2.5 * 0.15  # 4.5-7.0 maps to 0.7-0.85
    else:
        score_val = 0.85 + (ratio - 7.0) / 14.0 * 0.15  # 7.0-21.0 maps to 0.85-1.0

    return {
        "ratio": round(ratio, 2),
        "aa_pass": aa_pass,
        "aaa_pass": aaa_pass,
        "score": round(max(0.0, min(1.0, score_val)), 2),
    }
