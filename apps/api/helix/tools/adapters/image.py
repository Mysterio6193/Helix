"""Image generation adapters: OpenAI gpt-image-1, Replicate Flux + SDXL."""
from __future__ import annotations

import asyncio
import base64
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.core.storage import S3Storage
from helix.tools.base import Tool, ToolResult


async def _upload(bytes_: bytes, ext: str = "png", prefix: str = "generated") -> tuple[str, int, int]:
    storage = S3Storage()
    key = storage.make_key(prefix, ext)
    await asyncio.to_thread(storage.put_bytes, key, bytes_, content_type=f"image/{ext}")
    # Best-effort dimensions
    width = height = 0
    try:
        from io import BytesIO

        from PIL import Image

        img = Image.open(BytesIO(bytes_))
        width, height = img.size
    except Exception:
        pass
    return key, width, height


class OpenAIImageTool(Tool):
    name = "openai_image"
    description = "OpenAI gpt-image-1 image generation."

    async def _call(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1,
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.openai_api_key:
            return ToolResult(ok=False, error="OPENAI_API_KEY not configured")
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )
        keys: list[dict[str, Any]] = []
        for item in resp.data:
            if getattr(item, "b64_json", None):
                raw = base64.b64decode(item.b64_json)
            elif getattr(item, "url", None):
                async with httpx.AsyncClient(timeout=60) as http:
                    r = await http.get(item.url)
                    r.raise_for_status()
                    raw = r.content
            else:
                continue
            key, w, h = await _upload(raw, ext="png", prefix="openai_image")
            keys.append({"s3_key": key, "width": w, "height": h})
        return ToolResult(
            ok=True,
            data=keys,
            model="gpt-image-1",
            metadata={"prompt": prompt, "size": size, "quality": quality},
        )


class _ReplicateTool(Tool):
    REPLICATE_MODEL: str = ""
    name = "replicate_base"

    async def _call(self, *, prompt: str, **kwargs: Any) -> ToolResult:
        settings = get_settings()
        if not settings.replicate_api_token:
            return ToolResult(ok=False, error="REPLICATE_API_TOKEN not configured")
        try:
            import replicate
        except ImportError:
            return ToolResult(ok=False, error="replicate package not installed")

        client = replicate.Client(api_token=settings.replicate_api_token)
        input_payload: dict[str, Any] = {"prompt": prompt}
        input_payload.update({k: v for k, v in kwargs.items() if v is not None})

        # replicate-python is sync; offload to thread.
        import asyncio

        output = await asyncio.to_thread(client.run, self.REPLICATE_MODEL, input=input_payload)
        urls = output if isinstance(output, list) else [output]
        keys: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=120) as http:
            for url in urls:
                if not isinstance(url, str):
                    continue
                r = await http.get(url)
                r.raise_for_status()
                key, w, h = await _upload(r.content, ext="png", prefix=self.name)
                keys.append({"s3_key": key, "width": w, "height": h, "source_url": url})
        return ToolResult(ok=True, data=keys, model=self.REPLICATE_MODEL)


class FluxImageTool(_ReplicateTool):
    name = "flux_image"
    description = "Black Forest Labs Flux (Pro) via Replicate."
    REPLICATE_MODEL = "black-forest-labs/flux-1.1-pro"


class FluxSchnellTool(_ReplicateTool):
    name = "flux_schnell"
    description = "Black Forest Labs Flux Schnell — fast iteration."
    REPLICATE_MODEL = "black-forest-labs/flux-schnell"


class SDXLImageTool(_ReplicateTool):
    name = "sdxl_image"
    description = "Stability SDXL via Replicate."
    REPLICATE_MODEL = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"
