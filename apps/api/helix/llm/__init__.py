"""Centralized LLM / image / video model gateway.

Higgsfield-style: users pick a model from a curated catalog; API keys live
server-side in `Settings`. The gateway hides provider differences behind one
async surface (`complete`, `generate_image`, `stream_complete`).
"""
from helix.llm.catalog import (
    MODEL_CATALOG,
    ModelSpec,
    available_models,
    get_model,
    list_chat_models,
    list_image_models,
    list_video_models,
)
from helix.llm.gateway import (
    GatewayError,
    VideoResult,
    complete,
    generate_image,
    generate_video,
    stream_complete,
)

__all__ = [
    "MODEL_CATALOG",
    "ModelSpec",
    "VideoResult",
    "available_models",
    "get_model",
    "list_chat_models",
    "list_image_models",
    "list_video_models",
    "complete",
    "generate_image",
    "generate_video",
    "stream_complete",
    "GatewayError",
]
