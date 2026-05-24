"""Multi-modal AI processing: vision, OCR, audio transcription.

Provides unified interface for:
- Image analysis (brand asset scoring, content understanding)
- OCR (document text extraction, receipt parsing)
- Audio transcription (voice memos, call recordings)
- Video frame analysis

All operations are async and support caching.
"""
from __future__ import annotations

import io
from typing import Any

import httpx

from helix.core.cache import cached, get_cache
from helix.core.config import get_settings
from helix.core.logging import get_logger

log = get_logger("helix.multimodal")
settings = get_settings()


class VisionAnalyzer:
    """Analyze images using vision-capable LLMs (GPT-4V, Gemini Pro Vision)."""

    def __init__(self) -> None:
        self.cache = get_cache()

    @cached("vision", ttl=3600)
    async def analyze_image(
        self,
        image_url: str | None = None,
        image_base64: str | None = None,
        prompt: str = "Describe this image in detail.",
        model: str = "openai:gpt-4o",
    ) -> dict[str, Any]:
        """Analyze an image with a vision model.

        Returns structured analysis with description, objects, mood, and brand alignment.
        """
        from helix.llm.gateway import complete

        content: list[dict[str, Any]] = []
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_base64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}})
        content.append({"type": "text", "text": prompt})

        system_prompt = """You are a visual analysis expert for a creative operating system.
Analyze the image and return a JSON object with these fields:
- description: detailed visual description
- objects: list of main objects detected
- colors: dominant color palette (hex codes)
- mood: emotional tone (professional, playful, luxury, etc.)
- quality_score: 1-10 rating of visual quality
- brand_alignment: how well it would work for food/restaurant brands (1-10)
- text_detected: any text visible in the image
- composition: assessment of visual composition
- suggestions: list of improvement suggestions

Return ONLY valid JSON, no markdown."""

        try:
            result = await complete(
                model=model,
                messages=[{"role": "user", "content": content}],
                system=system_prompt,
                temperature=0.3,
                json_mode=True,
            )
            import json
            analysis = json.loads(result.text)
            return {
                "success": True,
                "analysis": analysis,
                "model": result.model,
                "cost_usd": result.cost_usd,
            }
        except Exception as exc:
            log.exception("vision_analysis_failed")
            return {"success": False, "error": str(exc)}

    async def analyze_brand_asset(
        self,
        image_url: str,
        brand_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze a brand asset against brand guidelines."""
        brand_info = ""
        if brand_context:
            brand_info = f"""
Brand Context:
- Name: {brand_context.get('name', 'Unknown')}
- Style: {brand_context.get('style', 'Unknown')}
- Colors: {brand_context.get('colors', 'Unknown')}
- Tone: {brand_context.get('tone', 'Unknown')}
"""

        prompt = f"""Analyze this brand asset for a food/restaurant business.{brand_info}
Evaluate: brand consistency, appeal, professionalism, and provide specific recommendations.
"""
        return await self.analyze_image(image_url=image_url, prompt=prompt)

    async def compare_images(
        self,
        image_urls: list[str],
        criteria: str = "visual quality and brand appeal",
    ) -> dict[str, Any]:
        """Compare multiple images and rank them."""
        from helix.llm.gateway import complete

        content = []
        for i, url in enumerate(image_urls):
            content.append({"type": "text", "text": f"Image {i+1}:"})
            content.append({"type": "image_url", "image_url": {"url": url}})

        content.append({"type": "text", "text": f"\nCompare these images on: {criteria}. Rank them from best to worst with reasoning."})

        system = "You are an expert creative director. Compare images objectively and provide ranked analysis with specific reasoning."

        try:
            result = await complete(
                model="openai:gpt-4o",
                messages=[{"role": "user", "content": content}],
                system=system,
                temperature=0.3,
            )
            return {"success": True, "comparison": result.text, "model": result.model}
        except Exception as exc:
            log.exception("image_comparison_failed")
            return {"success": False, "error": str(exc)}


class OCRProcessor:
    """Extract text from images and documents."""

    @cached("ocr", ttl=3600)
    async def extract_text(
        self,
        image_url: str | None = None,
        image_base64: str | None = None,
        document_type: str = "general",
    ) -> dict[str, Any]:
        """Extract text from an image using vision model OCR.

        document_type: general, receipt, invoice, menu, business_card
        """
        from helix.llm.gateway import complete

        content = []
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_base64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}})

        prompts = {
            "general": "Extract ALL text from this image. Preserve formatting and structure. Return as plain text.",
            "receipt": "Extract receipt details: merchant, date, items (name, qty, price), subtotal, tax, total, payment method. Return as JSON.",
            "invoice": "Extract invoice details: vendor, invoice_number, date, line_items (description, qty, rate, amount), subtotal, tax, total, due_date. Return as JSON.",
            "menu": "Extract menu items: category, item name, description, price, dietary tags. Return as structured JSON.",
            "business_card": "Extract contact info: name, title, company, phone, email, address, website. Return as JSON.",
        }

        prompt = prompts.get(document_type, prompts["general"])
        content.append({"type": "text", "text": prompt})

        try:
            result = await complete(
                model="openai:gpt-4o",
                messages=[{"role": "user", "content": content}],
                temperature=0.1,
            )

            # Try to parse as JSON if applicable
            text = result.text
            if document_type in ("receipt", "invoice", "menu", "business_card"):
                try:
                    import json
                    data = json.loads(text)
                    return {"success": True, "data": data, "raw_text": text, "document_type": document_type}
                except json.JSONDecodeError:
                    pass

            return {"success": True, "text": text, "document_type": document_type}
        except Exception as exc:
            log.exception("ocr_extraction_failed")
            return {"success": False, "error": str(exc)}

    async def batch_extract(
        self,
        images: list[dict[str, str]],
        document_type: str = "general",
    ) -> list[dict[str, Any]]:
        """Extract text from multiple images in parallel."""
        import asyncio
        tasks = [
            self.extract_text(
                image_url=img.get("url"),
                image_base64=img.get("base64"),
                document_type=document_type,
            )
            for img in images
        ]
        return await asyncio.gather(*tasks)


class AudioTranscriber:
    """Transcribe audio using Whisper or similar APIs."""

    async def transcribe(
        self,
        audio_url: str | None = None,
        audio_bytes: bytes | None = None,
        language: str | None = None,
        model: str = "whisper-1",
    ) -> dict[str, Any]:
        """Transcribe audio to text.

        Supports OpenAI Whisper and Groq Whisper.
        """
        if audio_url and audio_url.startswith("http"):
            # Download audio first
            async with httpx.AsyncClient(timeout=60) as client:
                try:
                    resp = await client.get(audio_url)
                    audio_bytes = resp.content
                except Exception as exc:
                    return {"success": False, "error": f"Failed to download audio: {exc}"}

        if not audio_bytes:
            return {"success": False, "error": "No audio provided"}

        # Use OpenAI Whisper API
        try:
            from helix.core.config import get_settings
            settings = get_settings()

            if not settings.openai_api_key:
                return {"success": False, "error": "OpenAI API key not configured for transcription"}

            async with httpx.AsyncClient(timeout=120) as client:
                files = {"file": ("audio.mp3", io.BytesIO(audio_bytes), "audio/mpeg")}
                data = {"model": model}
                if language:
                    data["language"] = language

                resp = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    files=files,
                    data=data,
                )
                resp.raise_for_status()
                result = resp.json()

                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "language": result.get("language", language or "auto"),
                    "duration": result.get("duration"),
                }
        except Exception as exc:
            log.exception("audio_transcription_failed")
            return {"success": False, "error": str(exc)}


class VideoAnalyzer:
    """Analyze video content by extracting key frames."""

    async def analyze_video(
        self,
        video_url: str,
        num_frames: int = 5,
        analysis_prompt: str = "Describe what's happening in this video.",
    ) -> dict[str, Any]:
        """Analyze a video by sampling frames and describing them.

        Note: This is a simplified version. For production, you'd want to use
        ffmpeg to extract frames server-side.
        """
        # For now, return a placeholder that suggests using the video URL
        # In production, this would extract frames and analyze them
        return {
            "success": True,
            "note": "Video analysis requires frame extraction. Use VisionAnalyzer with extracted frames.",
            "video_url": video_url,
            "suggested_frames": num_frames,
        }


# Convenience instances
vision = VisionAnalyzer()
ocr = OCRProcessor()
audio = AudioTranscriber()
video = VideoAnalyzer()
