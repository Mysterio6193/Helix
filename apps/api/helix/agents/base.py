"""Agent base class.

An Agent is a thin orchestrator that:
  1. Reads + writes `HelixState` (the LangGraph state TypedDict)
  2. Selects + invokes one or more `Skill` handlers
  3. Records a step + emits an event
  4. Persists artifacts via SQLAlchemy
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.db import session_factory
from helix.core.logging import get_logger
from helix.skills.base import SkillContext, SkillResult
from helix.skills.learning import format_learnings_preamble, load_learnings
from helix.skills.registry import get_handler, get_manifest
from helix.workflows.helpers import emit_event

log = get_logger(__name__)


@dataclass
class AgentContext:
    """What an agent receives at invocation time."""

    state: dict[str, Any]  # mutable HelixState dict
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def run_id(self) -> UUID:
        return UUID(self.state["run_id"])

    @property
    def brand_id(self) -> UUID:
        return UUID(self.state["brand_id"])

    @property
    def workspace_id(self) -> UUID:
        return UUID(self.state["workspace_id"])


@dataclass
class AgentResult:
    """What an agent returns. Merged back into HelixState by the workflow."""

    ok: bool
    patch: dict[str, Any] = field(default_factory=dict)
    skill_results: list[SkillResult] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    error: str | None = None


class Agent(ABC):
    """Base class for every Helix agent."""

    name: ClassVar[str] = "base"
    description: ClassVar[str] = ""

    @abstractmethod
    async def run(self, ctx: AgentContext) -> AgentResult:
        """Execute the agent's contribution to the workflow."""

    async def invoke_skill(
        self,
        ctx: AgentContext,
        *,
        skill_name: str,
        inputs: dict[str, Any] | None = None,
        session: AsyncSession | None = None,
    ) -> SkillResult:
        """Resolve handler + manifest, load learnings, invoke, emit event."""
        handler = get_handler(skill_name)
        manifest = get_manifest(skill_name)
        if handler is None or manifest is None:
            return SkillResult(ok=False, error=f"skill not registered: {skill_name}")

        if session is not None:
            return await self._invoke_with_session(
                session, ctx=ctx, skill_name=skill_name, handler=handler, inputs=inputs
            )
        async with session_factory() as sess:
            return await self._invoke_with_session(
                sess, ctx=ctx, skill_name=skill_name, handler=handler, inputs=inputs
            )

    async def _invoke_with_session(
        self,
        sess: AsyncSession,
        *,
        ctx: AgentContext,
        skill_name: str,
        handler,
        inputs: dict[str, Any] | None,
    ) -> SkillResult:
        learning_rows = await load_learnings(
            sess,
            skill_name=skill_name,
            brand_id=ctx.brand_id,
            brand_context_embedding=ctx.state.get("brand_context", {}).get("embedding"),
        )
        preamble = format_learnings_preamble(learning_rows)
        learning_texts = [preamble] if preamble else []

        skill_ctx = SkillContext(
            db=sess,
            brand_id=ctx.brand_id,
            workflow_run_id=ctx.run_id,
            task_id=None,
            workspace_id=ctx.workspace_id,
            brand_context=ctx.state.get("brand_context", {}),
            inputs=inputs or {},
            learnings=learning_texts,
        )
        started = time.time()
        try:
            result = await handler(skill_ctx)
        except Exception as exc:  # pragma: no cover
            log.exception("skill_invocation_failed", extra={"skill": skill_name})
            result = SkillResult(ok=False, error=f"{type(exc).__name__}: {exc}")

        await emit_event(
            run_id=ctx.run_id,
            kind="skill.completed" if result.ok else "skill.failed",
            payload={
                "agent": self.name,
                "skill": skill_name,
                "ok": result.ok,
                "cost_usd": result.cost_usd,
                "duration_ms": int((time.time() - started) * 1000),
                "error": result.error,
            },
        )

        # Score the Langfuse trace for this skill invocation
        from helix.core.observability import score_trace

        trace_id = ctx.state.get("langfuse_trace_id")
        if trace_id:
            score_trace(trace_id, f"skill:{skill_name}", 1.0 if result.ok else 0.0)

        return result

    async def run_agentic(
        self,
        ctx: AgentContext,
        *,
        system_prompt: str,
        allowed_skills: list[str] | None = None,
        allowed_tools: list[str] | None = None,
        max_steps: int = 8,
        tool_budget_usd: float = 1.00,
        llm_tool: str = "openai_chat",
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.4,
    ) -> AgentResult:
        """Execute a Hermes-style multi-step agentic loop for this agent."""
        from helix.agents.loop import AgenticLoop, LoopConfig

        cfg = LoopConfig(
            system_prompt=system_prompt,
            allowed_skills=allowed_skills,
            allowed_tools=allowed_tools,
            max_steps=max_steps,
            tool_budget_usd=tool_budget_usd,
            llm_tool=llm_tool,
            llm_model=llm_model,
            temperature=temperature,
        )
        loop = AgenticLoop(agent_name=self.name, config=cfg)
        return await loop.run(ctx)


_REGISTRY: dict[str, Agent] = {}


def register_agent(agent: Agent) -> Agent:
    _REGISTRY[agent.name] = agent
    return agent


def get_agent(name: str) -> Agent | None:
    return _REGISTRY.get(name)


def list_agents() -> list[Agent]:
    return list(_REGISTRY.values())


__all__ = [
    "Agent",
    "AgentContext",
    "AgentResult",
    "register_agent",
    "get_agent",
    "list_agents",
]
