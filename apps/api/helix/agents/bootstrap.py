"""Register all 9 Helix agents into the in-memory registry."""
from __future__ import annotations

from helix.agents.base import list_agents, register_agent
from helix.agents.brand_strategist import BrandStrategistAgent
from helix.agents.copywriter import CopywriterAgent
from helix.agents.creative_director import CreativeDirectorAgent
from helix.agents.critic import CriticAgent
from helix.agents.executive_council import ExecutiveCouncilAgent
from helix.agents.launch_manager import LaunchManagerAgent
from helix.agents.orchestrator import OrchestratorAgent
from helix.agents.packaging_designer import PackagingDesignerAgent
from helix.agents.social_producer import SocialProducerAgent
from helix.agents.visual_designer import VisualDesignerAgent
from helix.agents.web_builder import WebBuilderAgent
from helix.core.logging import get_logger

log = get_logger(__name__)


_BUILTINS = (
    OrchestratorAgent,
    BrandStrategistAgent,
    CreativeDirectorAgent,
    CopywriterAgent,
    VisualDesignerAgent,
    PackagingDesignerAgent,
    WebBuilderAgent,
    SocialProducerAgent,
    LaunchManagerAgent,
    CriticAgent,
    ExecutiveCouncilAgent,
)


def bootstrap_agents() -> list[str]:
    for cls in _BUILTINS:
        register_agent(cls())
    names = [a.name for a in list_agents()]
    log.info("agents_bootstrapped", count=len(names), names=names)
    return names


if __name__ == "__main__":
    names = bootstrap_agents()
    print(f"Registered {len(names)} agents:")
    for n in names:
        print(f"  - {n}")
