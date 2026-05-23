"""Register all built-in tool adapters into the registry.

Run as `python -m helix.tools.bootstrap` to populate the registry at startup.
Also invoked from the FastAPI lifespan.
"""
from __future__ import annotations

from helix.core.logging import get_logger
from helix.tools.adapters.deploy import GithubRepoTool, VercelDeployTool
from helix.tools.adapters.image import (
    FluxImageTool,
    FluxSchnellTool,
    OpenAIImageTool,
    SDXLImageTool,
)
from helix.tools.adapters.llm import (
    AnthropicChatTool,
    GeminiChatTool,
    OpenAIChatTool,
    OpenRouterChatTool,
)
from helix.tools.adapters.productivity import (
    CanvaConnectTool,
    FigmaApiTool,
    GmailDraftTool,
    NotionApiTool,
    WebSearchTool,
)
from helix.tools.adapters.browser_automation import BrowserUseTool, StagehandTool
from helix.tools.adapters.storage import PgvectorMemoryTool, S3StorageTool
from helix.tools.registry import clear_registry, list_tools, register_tool

log = get_logger(__name__)


_BUILTINS = (
    # LLM
    OpenAIChatTool,
    AnthropicChatTool,
    GeminiChatTool,
    OpenRouterChatTool,
    # Image
    OpenAIImageTool,
    FluxImageTool,
    FluxSchnellTool,
    SDXLImageTool,
    # Deploy
    GithubRepoTool,
    VercelDeployTool,
    # Productivity
    CanvaConnectTool,
    FigmaApiTool,
    NotionApiTool,
    GmailDraftTool,
    WebSearchTool,
    # Storage / memory
    S3StorageTool,
    PgvectorMemoryTool,
    # Browser Automation
    BrowserUseTool,
    StagehandTool,
)


def bootstrap_tools(*, reset: bool = False) -> list[str]:
    """Instantiate and register every built-in tool. Returns registered names."""
    if reset:
        clear_registry()
    for cls in _BUILTINS:
        try:
            register_tool(cls())
        except Exception:
            log.exception("tool_register_failed", extra={"tool": cls.__name__})
    names = [t.name for t in list_tools()]
    log.info("tools_bootstrapped", extra={"count": len(names), "names": names})
    return names


if __name__ == "__main__":
    names = bootstrap_tools(reset=True)
    print(f"Registered {len(names)} tools:")
    for n in names:
        print(f"  - {n}")
