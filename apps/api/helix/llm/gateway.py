"""Unified LLM / image gateway.

One function each for `complete`, `stream_complete`, `generate_image`. Routes
to the right adapter based on the catalog. All API keys are read server-side
from `Settings` — callers never need to pass a key.
"""
from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.llm.catalog import ModelSpec, default_model, get_model

log = get_logger(__name__)


class GatewayError(RuntimeError):
    pass


@dataclass
class ChatResult:
    text: str
    model: str
    provider: str
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float | None
    raw: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": self.cost_usd,
        }


@dataclass
class ImageResult:
    images: list[dict[str, Any]]  # [{s3_key, width, height, source_url?}, ...]
    model: str
    provider: str
    cost_usd: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "images": self.images,
            "model": self.model,
            "provider": self.provider,
            "cost_usd": self.cost_usd,
        }


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------
def _resolve(model_id: str | None, capability: str) -> ModelSpec:
    if model_id:
        spec = get_model(model_id)
        if not spec:
            raise GatewayError(f"unknown model id: {model_id}")
        if spec.capability != capability:
            raise GatewayError(
                f"model {model_id} is a {spec.capability} model, not {capability}"
            )
        return spec
    spec = default_model(capability)  # type: ignore[arg-type]
    if not spec:
        raise GatewayError(f"no default model registered for capability {capability}")
    return spec


def _require_key(spec: ModelSpec) -> str:
    attr = spec.settings_attr
    if not attr:
        return ""
    key = getattr(get_settings(), attr, "")
    if not key:
        raise GatewayError(
            f"server missing {attr.upper()} — model {spec.id} unavailable"
        )
    return key


def _estimate_chat_cost(spec: ModelSpec, prompt_tok: int, completion_tok: int) -> float:
    return (
        prompt_tok * spec.input_price_per_1k + completion_tok * spec.output_price_per_1k
    ) / 1000.0


# ---------------------------------------------------------------------------
# Chat completion
# ---------------------------------------------------------------------------
async def complete(
    *,
    model: str | None = None,
    prompt: str | None = None,
    messages: list[dict[str, Any]] | None = None,
    system: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    json_mode: bool = False,
) -> ChatResult:
    spec = _resolve(model, "chat")
    key = _require_key(spec)

    if spec.provider == "openai":
        return await _openai_chat(
            spec, key, prompt, messages, system, temperature, max_tokens, json_mode
        )
    if spec.provider == "anthropic":
        return await _anthropic_chat(
            spec, key, prompt, messages, system, temperature, max_tokens
        )
    if spec.provider == "gemini":
        return await _gemini_chat(
            spec, key, prompt, system, temperature, max_tokens
        )
    if spec.provider == "openrouter":
        return await _openrouter_chat(
            spec, key, prompt, messages, system, temperature, max_tokens
        )
    raise GatewayError(f"unsupported provider for chat: {spec.provider}")


async def stream_complete(
    *,
    model: str | None = None,
    prompt: str | None = None,
    messages: list[dict[str, Any]] | None = None,
    system: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> AsyncIterator[str]:
    """Yield text chunks as they arrive. Only OpenAI + Anthropic supported."""
    spec = _resolve(model, "chat")
    if not spec.supports_streaming:
        raise GatewayError(f"model {spec.id} does not support streaming")
    key = _require_key(spec)

    if spec.provider == "openai":
        async for chunk in _openai_stream(spec, key, prompt, messages, system, temperature, max_tokens):
            yield chunk
        return
    if spec.provider == "anthropic":
        async for chunk in _anthropic_stream(spec, key, prompt, messages, system, temperature, max_tokens):
            yield chunk
        return
    raise GatewayError(f"streaming not supported for provider {spec.provider}")


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
async def generate_image(
    *,
    model: str | None = None,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high",
    n: int = 1,
    s3_prefix: str = "generated",
    **provider_kwargs: Any,
) -> ImageResult:
    spec = _resolve(model, "image")
    key = _require_key(spec)

    if spec.provider == "openai":
        return await _openai_image(spec, key, prompt, size, quality, n, s3_prefix)
    if spec.provider == "replicate":
        return await _replicate_image(spec, key, prompt, s3_prefix, provider_kwargs)
    raise GatewayError(f"unsupported provider for image: {spec.provider}")


# ---------------------------------------------------------------------------
# Provider implementations — kept thin; reuse existing adapter logic.
# ---------------------------------------------------------------------------
async def _openai_chat(
    spec: ModelSpec,
    key: str,
    prompt: str | None,
    messages: list[dict[str, Any]] | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> ChatResult:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=key)
    msgs: list[dict[str, Any]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    if messages:
        msgs.extend(messages)
    elif prompt:
        msgs.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = {
        "model": spec.model,
        "messages": msgs,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode and spec.supports_json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = await client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content or ""
    usage = resp.usage
    cost = (
        _estimate_chat_cost(spec, usage.prompt_tokens or 0, usage.completion_tokens or 0)
        if usage
        else None
    )
    return ChatResult(
        text=text,
        model=spec.model,
        provider=spec.provider,
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
        cost_usd=cost,
    )


async def _openai_stream(
    spec: ModelSpec,
    key: str,
    prompt: str | None,
    messages: list[dict[str, Any]] | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=key)
    msgs: list[dict[str, Any]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    if messages:
        msgs.extend(messages)
    elif prompt:
        msgs.append({"role": "user", "content": prompt})

    stream = await client.chat.completions.create(
        model=spec.model,
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    async for event in stream:
        delta = event.choices[0].delta.content if event.choices else None
        if delta:
            yield delta


async def _anthropic_chat(
    spec: ModelSpec,
    key: str,
    prompt: str | None,
    messages: list[dict[str, Any]] | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
) -> ChatResult:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=key)
    msgs = messages or [{"role": "user", "content": prompt or ""}]
    kwargs: dict[str, Any] = {
        "model": spec.model,
        "messages": msgs,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if system:
        kwargs["system"] = system

    resp = await client.messages.create(**kwargs)
    text = "".join(
        block.text for block in resp.content if getattr(block, "type", "") == "text"
    )
    usage = resp.usage
    cost = (
        _estimate_chat_cost(spec, usage.input_tokens, usage.output_tokens) if usage else None
    )
    return ChatResult(
        text=text,
        model=spec.model,
        provider=spec.provider,
        prompt_tokens=usage.input_tokens if usage else None,
        completion_tokens=usage.output_tokens if usage else None,
        cost_usd=cost,
    )


async def _anthropic_stream(
    spec: ModelSpec,
    key: str,
    prompt: str | None,
    messages: list[dict[str, Any]] | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=key)
    msgs = messages or [{"role": "user", "content": prompt or ""}]
    kwargs: dict[str, Any] = {
        "model": spec.model,
        "messages": msgs,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if system:
        kwargs["system"] = system

    async with client.messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            yield text


async def _gemini_chat(
    spec: ModelSpec,
    key: str,
    prompt: str | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
) -> ChatResult:
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover
        raise GatewayError("google-genai not installed") from exc

    client = genai.Client(api_key=key)
    contents = (system + "\n\n" + (prompt or "")) if system else (prompt or "")
    resp = await client.aio.models.generate_content(
        model=spec.model,
        contents=contents,
        config={"temperature": temperature, "max_output_tokens": max_tokens},
    )
    text = resp.text or ""
    return ChatResult(
        text=text,
        model=spec.model,
        provider=spec.provider,
        prompt_tokens=None,
        completion_tokens=None,
        cost_usd=None,
    )


async def _openrouter_chat(
    spec: ModelSpec,
    key: str,
    prompt: str | None,
    messages: list[dict[str, Any]] | None,
    system: str | None,
    temperature: float,
    max_tokens: int,
) -> ChatResult:
    msgs: list[dict[str, Any]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    if messages:
        msgs.extend(messages)
    elif prompt:
        msgs.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "X-Title": "Helix",
            },
            json={
                "model": spec.model,
                "messages": msgs,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        body = resp.json()
    text = body["choices"][0]["message"]["content"]
    usage = body.get("usage", {}) or {}
    p, c = usage.get("prompt_tokens"), usage.get("completion_tokens")
    cost = _estimate_chat_cost(spec, p or 0, c or 0) if (p and c) else None
    return ChatResult(
        text=text, model=spec.model, provider=spec.provider,
        prompt_tokens=p, completion_tokens=c, cost_usd=cost,
    )


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------
async def _upload_image(raw: bytes, ext: str, prefix: str) -> dict[str, Any]:
    from helix.core.storage import S3Storage

    storage = S3Storage()
    key = storage.make_key(prefix, ext)
    storage.put_bytes(key, raw, content_type=f"image/{ext}")
    width = height = 0
    try:
        from io import BytesIO

        from PIL import Image

        img = Image.open(BytesIO(raw))
        width, height = img.size
    except Exception:
        pass
    return {"s3_key": key, "width": width, "height": height}


async def _openai_image(
    spec: ModelSpec,
    key: str,
    prompt: str,
    size: str,
    quality: str,
    n: int,
    s3_prefix: str,
) -> ImageResult:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=key)
    resp = await client.images.generate(
        model=spec.model, prompt=prompt, size=size, quality=quality, n=n
    )
    images: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=60) as http:
        for item in resp.data:
            raw: bytes
            if getattr(item, "b64_json", None):
                raw = base64.b64decode(item.b64_json)
            elif getattr(item, "url", None):
                r = await http.get(item.url)
                r.raise_for_status()
                raw = r.content
            else:
                continue
            images.append(await _upload_image(raw, "png", s3_prefix))
    cost = (spec.price_per_image or 0.0) * len(images)
    return ImageResult(
        images=images, model=spec.model, provider=spec.provider, cost_usd=cost or None
    )


async def _replicate_image(
    spec: ModelSpec,
    key: str,
    prompt: str,
    s3_prefix: str,
    extra: dict[str, Any],
) -> ImageResult:
    try:
        import replicate
    except ImportError as exc:
        raise GatewayError("replicate package not installed") from exc

    client = replicate.Client(api_token=key)
    payload: dict[str, Any] = {"prompt": prompt}
    payload.update({k: v for k, v in extra.items() if v is not None})

    output = await asyncio.to_thread(client.run, spec.model, input=payload)
    urls = output if isinstance(output, list) else [output]
    images: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=120) as http:
        for url in urls:
            if not isinstance(url, str):
                continue
            r = await http.get(url)
            r.raise_for_status()
            uploaded = await _upload_image(r.content, "png", s3_prefix)
            uploaded["source_url"] = url
            images.append(uploaded)
    cost = (spec.price_per_image or 0.0) * len(images)
    return ImageResult(
        images=images, model=spec.model, provider=spec.provider, cost_usd=cost or None
    )
