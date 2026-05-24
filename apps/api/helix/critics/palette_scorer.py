"""Image color palette adherence scorer using PIL."""
from __future__ import annotations

import io
import math

import httpx
from PIL import Image

from helix.core.logging import get_logger
from helix.tools.registry import get_tool

log = get_logger(__name__)


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Parse hex color (with or without #) to RGB tuple."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """Compute Euclidean distance between two colors in RGB space (normalized 0.0 - 1.0)."""
    dist = math.sqrt(
        (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2
    )
    # Max possible distance is sqrt(255^2 * 3) = 441.67
    return dist / 441.67


def _extract_dominant_colors(img_bytes: bytes, max_colors: int = 5) -> list[tuple[int, int, int]]:
    """Extract dominant colors using Pillow's fast color quantization."""
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        # Resize image to a small square to speed up and smooth out details
        img = img.resize((32, 32), Image.Resampling.NEAREST)
        
        # Quantize the image down to the target number of colors
        quantized = img.quantize(colors=max_colors)
        
        # Get palette colors
        palette = quantized.getpalette()
        if not palette:
            return []
            
        colors = []
        for i in range(max_colors):
            r = palette[i * 3]
            g = palette[i * 3 + 1]
            b = palette[i * 3 + 2]
            colors.append((r, g, b))
        return colors
    except Exception as exc:
        log.warning("palette_scorer.extract_failed", error=str(exc))
        return []


async def score_palette(
    image_data: bytes | str,
    target_palette: list[str],
    trace_id: str | None = None,
) -> float:
    """Score adherence of an image's dominant colors to a target brand palette.

    Returns:
        float: Adherence score between 0.0 (totally different) and 1.0 (perfect match).
    """
    if not target_palette:
        return 1.0

    img_bytes = None

    # Handle inputs
    if isinstance(image_data, bytes):
        img_bytes = image_data
    elif isinstance(image_data, str):
        try:
            if image_data.startswith("http"):
                # Download URL
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(image_data)
                    if resp.status_code == 200:
                        img_bytes = resp.content
            elif image_data.startswith("data:"):
                # Data URL
                import base64
                header, encoded = image_data.split(",", 1)
                img_bytes = base64.b64decode(encoded)
            else:
                # Try fetching S3 key using s3_storage tool
                s3_tool = get_tool("s3_storage")
                if s3_tool:
                    res = await s3_tool.call(trace_id=trace_id, action="get", key=image_data)
                    if res.ok and res.data:
                        img_bytes = res.data
        except Exception as exc:
            log.warning("palette_scorer.fetch_failed", error=str(exc))

    if not img_bytes:
        log.warning("palette_scorer.no_image_bytes")
        return 0.8  # Fallback

    dominant_colors = _extract_dominant_colors(img_bytes, max_colors=len(target_palette))
    if not dominant_colors:
        return 0.8

    # Parse target colors
    targets = []
    for c in target_palette:
        try:
            targets.append(_hex_to_rgb(c))
        except Exception:
            continue

    if not targets:
        return 1.0

    # Calculate average minimum distance: for each dominant color, find the closest target color
    total_min_dist = 0.0
    for dom in dominant_colors:
        min_dist = min(_color_distance(dom, tgt) for tgt in targets)
        total_min_dist += min_dist

    avg_dist = total_min_dist / len(dominant_colors)
    
    # Invert to get score (lower distance = higher score)
    score_val = 1.0 - avg_dist
    return max(0.0, min(1.0, score_val))
