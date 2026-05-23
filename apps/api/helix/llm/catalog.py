"""Curated model catalog — the source of truth for what users can pick.

Each entry advertises capability, provider, pricing, context window, tier and
default-ness. Availability is computed at runtime by checking whether the
server has the matching API key configured (no per-user key entry needed —
Higgsfield-style).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from helix.core.config import get_settings

Capability = Literal["chat", "image", "video", "embedding"]
Tier = Literal["free", "pro", "team"]


@dataclass(frozen=True)
class ModelSpec:
    id: str  # public id used by clients (e.g. "openai:gpt-4o-mini")
    provider: str  # "openai" | "anthropic" | "gemini" | "openrouter" | "replicate" | "runway" | "veo"
    model: str  # provider-native model name passed to the SDK
    display_name: str
    capability: Capability
    description: str
    context_window: int | None = None
    max_output_tokens: int | None = None
    input_price_per_1k: float = 0.0  # USD per 1k input tokens (chat) or per image (image)
    output_price_per_1k: float = 0.0  # USD per 1k output tokens
    price_per_image: float | None = None  # for image models
    price_per_second: float | None = None  # for video models
    tier: Tier = "pro"
    is_default: bool = False
    supports_streaming: bool = False
    supports_json_mode: bool = False
    supports_vision: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)
    requires_setting: str = ""  # name of Settings attr that must be truthy

    @property
    def settings_attr(self) -> str:
        if self.requires_setting:
            return self.requires_setting
        # default mapping
        return {
            "openai": "openai_api_key",
            "anthropic": "anthropic_api_key",
            "gemini": "gemini_api_key",
            "openrouter": "openrouter_api_key",
            "replicate": "replicate_api_token",
            "runway": "runway_api_key",
            "veo": "google_veo_api_key",
        }.get(self.provider, "")


# ---------------------------------------------------------------------------
# Chat models
# ---------------------------------------------------------------------------
_CHAT_MODELS: list[ModelSpec] = [
    # ── OpenAI (latest) ─────────────────────────────────────────────────
    ModelSpec(
        id="openai:gpt-5",
        provider="openai",
        model="gpt-5",
        display_name="GPT-5",
        capability="chat",
        description="OpenAI's newest flagship — top reasoning, vision, and tool use.",
        context_window=400_000,
        max_output_tokens=32_000,
        input_price_per_1k=0.00125,
        output_price_per_1k=0.01,
        tier="pro",
        supports_streaming=True,
        supports_json_mode=True,
        supports_vision=True,
        tags=("latest", "flagship", "vision", "reasoning"),
    ),
    ModelSpec(
        id="openai:gpt-5-mini",
        provider="openai",
        model="gpt-5-mini",
        display_name="GPT-5 mini",
        capability="chat",
        description="Newest small OpenAI model — fast, cheap, GPT-5-class quality.",
        context_window=400_000,
        max_output_tokens=32_000,
        input_price_per_1k=0.00025,
        output_price_per_1k=0.002,
        tier="free",
        is_default=True,
        supports_streaming=True,
        supports_json_mode=True,
        supports_vision=True,
        tags=("latest", "cheap", "fast", "default"),
    ),
    ModelSpec(
        id="openai:o3",
        provider="openai",
        model="o3",
        display_name="o3",
        capability="chat",
        description="OpenAI's deep-reasoning model — math, code, multi-step planning.",
        context_window=200_000,
        max_output_tokens=100_000,
        input_price_per_1k=0.002,
        output_price_per_1k=0.008,
        tier="pro",
        supports_streaming=True,
        supports_json_mode=True,
        tags=("latest", "reasoning", "deep-think"),
    ),
    ModelSpec(
        id="openai:o4-mini",
        provider="openai",
        model="o4-mini",
        display_name="o4 mini",
        capability="chat",
        description="Reasoning-tuned small model — cheap chain-of-thought.",
        context_window=200_000,
        max_output_tokens=100_000,
        input_price_per_1k=0.0011,
        output_price_per_1k=0.0044,
        tier="free",
        supports_streaming=True,
        supports_json_mode=True,
        tags=("latest", "reasoning", "cheap"),
    ),
    # ── OpenAI (legacy still supported) ─────────────────────────────────
    ModelSpec(
        id="openai:gpt-4o",
        provider="openai",
        model="gpt-4o",
        display_name="GPT-4o",
        capability="chat",
        description="Previous OpenAI flagship — still strong vision + JSON mode.",
        context_window=128_000,
        max_output_tokens=16_000,
        input_price_per_1k=0.0025,
        output_price_per_1k=0.01,
        tier="pro",
        supports_streaming=True,
        supports_json_mode=True,
        supports_vision=True,
        tags=("legacy", "vision"),
    ),
    ModelSpec(
        id="openai:gpt-4o-mini",
        provider="openai",
        model="gpt-4o-mini",
        display_name="GPT-4o mini",
        capability="chat",
        description="Previous-gen small model. Still cheap if you need 4o behavior.",
        context_window=128_000,
        max_output_tokens=16_000,
        input_price_per_1k=0.00015,
        output_price_per_1k=0.0006,
        tier="free",
        supports_streaming=True,
        supports_json_mode=True,
        supports_vision=True,
        tags=("legacy", "cheap", "fast"),
    ),
    # ── Anthropic (latest) ──────────────────────────────────────────────
    ModelSpec(
        id="anthropic:claude-opus-4-6",
        provider="anthropic",
        model="claude-opus-4-6",
        display_name="Claude Opus 4.6",
        capability="chat",
        description="Anthropic's newest flagship — best writing, reasoning, and brand voice.",
        context_window=200_000,
        max_output_tokens=64_000,
        input_price_per_1k=0.015,
        output_price_per_1k=0.075,
        tier="team",
        supports_streaming=True,
        supports_vision=True,
        tags=("latest", "flagship", "premium", "writing", "reasoning"),
    ),
    ModelSpec(
        id="anthropic:claude-sonnet-4-5",
        provider="anthropic",
        model="claude-sonnet-4-5",
        display_name="Claude Sonnet 4.5",
        capability="chat",
        description="Balanced Claude — agentic tool use + long-form copy.",
        context_window=200_000,
        max_output_tokens=64_000,
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier="pro",
        supports_streaming=True,
        supports_vision=True,
        tags=("latest", "balanced", "agents"),
    ),
    ModelSpec(
        id="anthropic:claude-haiku-4-5",
        provider="anthropic",
        model="claude-haiku-4-5",
        display_name="Claude Haiku 4.5",
        capability="chat",
        description="Fastest Claude — production volume copy, near-Sonnet quality.",
        context_window=200_000,
        max_output_tokens=64_000,
        input_price_per_1k=0.001,
        output_price_per_1k=0.005,
        tier="free",
        supports_streaming=True,
        supports_vision=True,
        tags=("latest", "cheap", "fast"),
    ),
    # ── Anthropic (legacy) ──────────────────────────────────────────────
    ModelSpec(
        id="anthropic:claude-3-5-sonnet",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        display_name="Claude 3.5 Sonnet",
        capability="chat",
        description="Previous-gen Claude — still strong writing model.",
        context_window=200_000,
        max_output_tokens=8_000,
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier="pro",
        supports_streaming=True,
        supports_vision=True,
        tags=("legacy", "writing"),
    ),
    ModelSpec(
        id="anthropic:claude-3-5-haiku",
        provider="anthropic",
        model="claude-3-5-haiku-latest",
        display_name="Claude 3.5 Haiku",
        capability="chat",
        description="Previous-gen small Claude. Cheap, fast.",
        context_window=200_000,
        max_output_tokens=8_000,
        input_price_per_1k=0.001,
        output_price_per_1k=0.005,
        tier="free",
        supports_streaming=True,
        tags=("legacy", "cheap"),
    ),
    # ── Gemini (latest) ─────────────────────────────────────────────────
    ModelSpec(
        id="gemini:gemini-2.5-pro",
        provider="gemini",
        model="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        capability="chat",
        description="Google's newest flagship — reasoning-first, 2M context window.",
        context_window=2_000_000,
        max_output_tokens=64_000,
        input_price_per_1k=0.00125,
        output_price_per_1k=0.01,
        tier="pro",
        supports_vision=True,
        tags=("latest", "flagship", "long-context", "reasoning"),
    ),
    ModelSpec(
        id="gemini:gemini-2.5-flash",
        provider="gemini",
        model="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        capability="chat",
        description="Cheapest top-tier model — huge context, blazing fast.",
        context_window=1_000_000,
        max_output_tokens=64_000,
        input_price_per_1k=0.0003,
        output_price_per_1k=0.0025,
        tier="free",
        supports_vision=True,
        tags=("latest", "cheap", "fast", "long-context"),
    ),
    # ── Gemini (legacy) ─────────────────────────────────────────────────
    ModelSpec(
        id="gemini:gemini-1.5-pro",
        provider="gemini",
        model="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        capability="chat",
        description="Previous-gen Google flagship with 2M context.",
        context_window=2_000_000,
        max_output_tokens=8_000,
        input_price_per_1k=0.00125,
        output_price_per_1k=0.005,
        tier="pro",
        supports_vision=True,
        tags=("legacy", "long-context"),
    ),
    ModelSpec(
        id="gemini:gemini-1.5-flash",
        provider="gemini",
        model="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        capability="chat",
        description="Previous-gen Flash. Cheap, very fast.",
        context_window=1_000_000,
        max_output_tokens=8_000,
        input_price_per_1k=0.000075,
        output_price_per_1k=0.0003,
        tier="free",
        tags=("legacy", "cheap", "fast"),
    ),
    # ── OpenRouter wildcard ────────────────────────────────────────────
    ModelSpec(
        id="openrouter:auto",
        provider="openrouter",
        model="openrouter/auto",
        display_name="Auto (OpenRouter)",
        capability="chat",
        description="OpenRouter picks the best model for your prompt.",
        context_window=128_000,
        input_price_per_1k=0.001,
        output_price_per_1k=0.004,
        tier="pro",
        tags=("auto",),
    ),
]


# ---------------------------------------------------------------------------
# Image models
# ---------------------------------------------------------------------------
_IMAGE_MODELS: list[ModelSpec] = [
    ModelSpec(
        id="image:gpt-image-1",
        provider="openai",
        model="gpt-image-1",
        display_name="GPT-Image-1",
        capability="image",
        description="OpenAI's image model — best text rendering and prompt adherence.",
        price_per_image=0.04,
        tier="pro",
        is_default=True,
        tags=("flagship", "text-in-image"),
    ),
    ModelSpec(
        id="image:flux-1.1-pro",
        provider="replicate",
        model="black-forest-labs/flux-1.1-pro",
        display_name="Flux 1.1 Pro",
        capability="image",
        description="Black Forest Labs Flux Pro via Replicate. Photo-real and stylized.",
        price_per_image=0.04,
        tier="pro",
        tags=("photo", "stylized"),
    ),
    ModelSpec(
        id="image:flux-schnell",
        provider="replicate",
        model="black-forest-labs/flux-schnell",
        display_name="Flux Schnell",
        capability="image",
        description="Fast variant — great for iterating on concepts.",
        price_per_image=0.003,
        tier="free",
        tags=("fast", "cheap"),
    ),
    ModelSpec(
        id="image:sdxl",
        provider="replicate",
        model="stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
        display_name="Stable Diffusion XL",
        capability="image",
        description="Stability SDXL — versatile open-weights model.",
        price_per_image=0.0035,
        tier="free",
        tags=("open-weights",),
    ),
]


# ---------------------------------------------------------------------------
# Video models
# ---------------------------------------------------------------------------
_VIDEO_MODELS: list[ModelSpec] = [
    ModelSpec(
        id="video:runway-gen3",
        provider="runway",
        model="gen3a_turbo",
        display_name="Runway Gen-3 Alpha Turbo",
        capability="video",
        description="Runway Gen-3 Turbo — cinematic 5–10s clips.",
        price_per_second=0.05,
        tier="team",
        tags=("cinematic",),
    ),
    ModelSpec(
        id="video:veo-3",
        provider="veo",
        model="veo-3.0-generate-preview",
        display_name="Google Veo 3",
        capability="video",
        description="Google's Veo 3 — high-fidelity short clips, native audio.",
        price_per_second=0.075,
        tier="team",
        is_default=True,
        tags=("flagship", "audio"),
    ),
]


MODEL_CATALOG: dict[str, ModelSpec] = {
    spec.id: spec
    for spec in (*_CHAT_MODELS, *_IMAGE_MODELS, *_VIDEO_MODELS)
}


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
def get_model(model_id: str) -> ModelSpec | None:
    return MODEL_CATALOG.get(model_id)


def _is_available(spec: ModelSpec) -> bool:
    """A model is available iff the server has the provider key configured."""
    attr = spec.settings_attr
    if not attr:
        return True
    settings = get_settings()
    return bool(getattr(settings, attr, ""))


def available_models(capability: Capability | None = None) -> list[ModelSpec]:
    specs = list(MODEL_CATALOG.values())
    if capability:
        specs = [s for s in specs if s.capability == capability]
    return [s for s in specs if _is_available(s)]


def list_chat_models(available_only: bool = True) -> list[ModelSpec]:
    return _maybe_filter(_CHAT_MODELS, available_only)


def list_image_models(available_only: bool = True) -> list[ModelSpec]:
    return _maybe_filter(_IMAGE_MODELS, available_only)


def list_video_models(available_only: bool = True) -> list[ModelSpec]:
    return _maybe_filter(_VIDEO_MODELS, available_only)


def _maybe_filter(specs: list[ModelSpec], available_only: bool) -> list[ModelSpec]:
    if not available_only:
        return list(specs)
    return [s for s in specs if _is_available(s)]


def default_model(capability: Capability) -> ModelSpec | None:
    """Pick the user-facing default for a capability.

    Preference order:
      1. A model marked `is_default=True` whose key is configured
      2. The first available model in that capability
      3. The first model in the catalog (even if key missing) — caller decides
    """
    pool = [s for s in MODEL_CATALOG.values() if s.capability == capability]
    available = [s for s in pool if _is_available(s)]
    for s in available:
        if s.is_default:
            return s
    if available:
        return available[0]
    for s in pool:
        if s.is_default:
            return s
    return pool[0] if pool else None
