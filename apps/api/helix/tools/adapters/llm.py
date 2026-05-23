"""LLM adapters: OpenAI Chat, Anthropic Claude, Google Gemini, OpenRouter."""
from __future__ import annotations

import json
from typing import Any

from helix.core.config import get_settings
from helix.tools.base import Tool, ToolResult

PRICING_PER_1K = {
    # rough, kept conservative; refresh as needed
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-3-5-sonnet-latest": (0.003, 0.015),
    "claude-3-5-sonnet-20241022": (0.003, 0.015),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-1.5-flash": (0.000075, 0.0003),
}


def _estimate_cost(model: str, prompt_tok: int, completion_tok: int) -> float:
    in_rate, out_rate = PRICING_PER_1K.get(model, (0.0, 0.0))
    return (prompt_tok * in_rate + completion_tok * out_rate) / 1000.0


class OpenAIChatTool(Tool):
    name = "openai_chat"
    description = "OpenAI chat completion (GPT-4o, GPT-4o-mini, etc.)."

    async def _call(
        self,
        *,
        prompt: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        model: str = "gpt-4o-mini",
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        json_mode: bool = False,
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.openai_api_key:
            return ToolResult(ok=False, error="OPENAI_API_KEY not configured")
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        msgs: list[dict[str, Any]] = []
        if system:
            msgs.append({"role": "system", "content": system})
        if messages:
            msgs.extend(messages)
        elif prompt:
            msgs.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        cost = _estimate_cost(model, usage.prompt_tokens or 0, usage.completion_tokens or 0) if usage else None
        data: Any = text
        if json_mode:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {"raw": text}
        return ToolResult(
            ok=True,
            data=data,
            model=model,
            cost_usd=cost,
            metadata={
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "raw_text": text,
            },
        )


class AnthropicChatTool(Tool):
    name = "anthropic_chat"
    description = "Anthropic Claude messages API."

    async def _call(
        self,
        *,
        prompt: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        model: str = "claude-3-5-sonnet-latest",
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.anthropic_api_key:
            return ToolResult(ok=False, error="ANTHROPIC_API_KEY not configured")
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        msgs = messages or [{"role": "user", "content": prompt or ""}]
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system

        resp = await client.messages.create(**kwargs)
        # resp.content is a list of TextBlock; concatenate text segments
        text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
        usage = resp.usage
        cost = _estimate_cost(model, usage.input_tokens, usage.output_tokens) if usage else None
        return ToolResult(
            ok=True,
            data=text,
            model=model,
            cost_usd=cost,
            metadata={
                "prompt_tokens": usage.input_tokens if usage else None,
                "completion_tokens": usage.output_tokens if usage else None,
            },
        )


class GeminiChatTool(Tool):
    name = "gemini_chat"
    description = "Google Gemini chat (genai SDK)."

    async def _call(
        self,
        *,
        prompt: str | None = None,
        model: str = "gemini-1.5-flash",
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.gemini_api_key:
            return ToolResult(ok=False, error="GEMINI_API_KEY not configured")
        try:
            from google import genai
        except ImportError:  # pragma: no cover
            return ToolResult(ok=False, error="google-genai not installed")

        client = genai.Client(api_key=settings.gemini_api_key)
        contents = (system + "\n\n" + (prompt or "")) if system else (prompt or "")
        # The SDK is async via aio
        resp = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        text = resp.text or ""
        return ToolResult(ok=True, data=text, model=model)


class OpenRouterChatTool(Tool):
    name = "openrouter_chat"
    description = "OpenRouter unified LLM gateway."

    async def _call(
        self,
        *,
        prompt: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        model: str = "openrouter/auto",
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.openrouter_api_key:
            return ToolResult(ok=False, error="OPENROUTER_API_KEY not configured")
        import httpx

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
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": msgs,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            body = resp.json()
        text = body["choices"][0]["message"]["content"]
        return ToolResult(ok=True, data=text, model=model)
