"""Agentic tool-use loop — Hermes-style reasoning loop for agents.

An ``AgenticLoop`` gives agents the ability to reason over multiple steps:
generate a plan, call tools/skills, observe results, iterate, and finalize.
The loop enforces budget, step limits, and emits granular events.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from helix.agents.base import AgentContext, AgentResult
from helix.core.logging import get_logger
from helix.core.observability import score_trace
from helix.skills.base import SkillResult
from helix.skills.registry import get_handler, list_manifests
from helix.tools.registry import get_tool, list_tools
from helix.workflows.helpers import emit_event

log = get_logger(__name__)


@dataclass
class LoopConfig:
    """Configuration for an agentic loop run."""

    system_prompt: str = ""
    allowed_skills: list[str] | None = None
    allowed_tools: list[str] | None = None
    max_steps: int = 8
    tool_budget_usd: float = 1.00
    llm_tool: str = "openai_chat"
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.4


@dataclass
class LoopStep:
    """Record of a single step in the agentic loop."""

    index: int
    action: str  # "thought" | "tool_call" | "skill_call" | "finalize"
    tool: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    duration_ms: int = 0


class AgenticLoop:
    """Multi-step reasoning loop for an agent.

    The loop uses an LLM to decide which tool/skill to invoke next, accumulates
    results, and terminates when the LLM calls ``finalize`` or limits are hit.
    """

    def __init__(self, agent_name: str, config: LoopConfig) -> None:
        self.agent_name = agent_name
        self.config = config

    async def run(self, ctx: AgentContext) -> AgentResult:
        """Execute the agentic loop and return a merged result."""
        cfg = self.config
        steps: list[LoopStep] = []
        total_cost = 0.0
        all_skill_results: list[SkillResult] = []
        all_artifact_ids: list[str] = []
        patch: dict[str, Any] = {}

        # Build tool catalog for the LLM
        catalog = self._build_catalog()
        conversation = self._init_conversation(ctx, catalog)

        for step_idx in range(cfg.max_steps):
            # Budget check
            if total_cost >= cfg.tool_budget_usd:
                log.info(
                    "agentic.budget_exceeded",
                    agent=self.agent_name,
                    cost=total_cost,
                    budget=cfg.tool_budget_usd,
                )
                break

            # Ask LLM for next action
            llm_tool = get_tool(cfg.llm_tool)
            if llm_tool is None:
                return AgentResult(
                    ok=False,
                    error=f"LLM tool not found: {cfg.llm_tool}",
                )

            started = time.time()
            llm_result = await llm_tool.call(
                trace_id=ctx.state.get("langfuse_trace_id"),
                messages=conversation,
                model=cfg.llm_model,
                temperature=cfg.temperature,
                max_tokens=2000,
                json_mode=True,
            )
            llm_cost = llm_result.cost_usd or 0.0
            total_cost += llm_cost

            if not llm_result.ok:
                log.warning("agentic.llm_failed", error=llm_result.error)
                break

            # Parse LLM response
            try:
                action = (
                    llm_result.data
                    if isinstance(llm_result.data, dict)
                    else json.loads(str(llm_result.data))
                )
            except (json.JSONDecodeError, TypeError):
                log.warning("agentic.parse_failed", raw=str(llm_result.data)[:500])
                # Append error and let LLM retry
                conversation.append({"role": "assistant", "content": str(llm_result.data)})
                conversation.append({
                    "role": "user",
                    "content": "Your response was not valid JSON. Please respond with a valid JSON object.",
                })
                continue

            # Emit thought event
            thought = action.get("thought", "")
            if thought:
                await emit_event(
                    run_id=ctx.run_id,
                    kind="agent.thought",
                    payload={"agent": self.agent_name, "step": step_idx, "thought": thought},
                )

            # Check for finalize
            if action.get("finalize"):
                outputs = action.get("outputs", {})
                patch.update(outputs)
                steps.append(LoopStep(
                    index=step_idx,
                    action="finalize",
                    result=outputs,
                    cost_usd=llm_cost,
                    duration_ms=int((time.time() - started) * 1000),
                ))
                await emit_event(
                    run_id=ctx.run_id,
                    kind="agent.finalize",
                    payload={"agent": self.agent_name, "step": step_idx, "outputs_keys": list(outputs.keys())},
                )
                break

            # Execute tool or skill call
            tool_name = action.get("tool")
            skill_name = action.get("skill")
            call_inputs = action.get("inputs", {})

            if skill_name:
                step_result = await self._invoke_skill(
                    ctx, skill_name, call_inputs, step_idx
                )
                total_cost += step_result.get("cost_usd", 0.0)
                if step_result.get("skill_result"):
                    all_skill_results.append(step_result["skill_result"])
                    all_artifact_ids.extend(
                        getattr(step_result["skill_result"], "artifact_ids", []) or []
                    )
                    # Merge skill outputs into patch
                    outputs = getattr(step_result["skill_result"], "outputs", {}) or {}
                    patch.update(outputs)
            elif tool_name:
                step_result = await self._invoke_tool(
                    ctx, tool_name, call_inputs, step_idx
                )
                total_cost += step_result.get("cost_usd", 0.0)
            else:
                step_result = {"ok": False, "error": "No tool, skill, or finalize specified"}

            steps.append(LoopStep(
                index=step_idx,
                action="skill_call" if skill_name else "tool_call",
                tool=skill_name or tool_name,
                inputs=call_inputs,
                result=step_result,
                cost_usd=step_result.get("cost_usd", 0.0),
                duration_ms=step_result.get("duration_ms", 0),
            ))

            # Add result to conversation for the LLM
            conversation.append({"role": "assistant", "content": json.dumps(action)})
            conversation.append({
                "role": "user",
                "content": json.dumps({
                    "observation": {
                        "ok": step_result.get("ok", False),
                        "summary": str(step_result.get("summary", ""))[:1000],
                        "remaining_budget_usd": round(cfg.tool_budget_usd - total_cost, 4),
                        "steps_remaining": cfg.max_steps - step_idx - 1,
                    }
                }),
            })

        # Build final result
        patch["total_cost_usd"] = (ctx.state.get("total_cost_usd") or 0.0) + total_cost

        # Score the trace
        trace_id = ctx.state.get("langfuse_trace_id")
        if trace_id:
            score_trace(trace_id, f"loop:{self.agent_name}:steps", float(len(steps)))
            score_trace(trace_id, f"loop:{self.agent_name}:cost", total_cost)

        return AgentResult(
            ok=True,
            patch=patch,
            skill_results=all_skill_results,
            artifact_ids=all_artifact_ids,
        )

    def _build_catalog(self) -> list[dict[str, Any]]:
        """Build a JSON-serializable catalog of available tools and skills."""
        catalog: list[dict[str, Any]] = []
        cfg = self.config

        # Tools
        for tool_name, tool in list_tools().items():
            if cfg.allowed_tools is not None and tool_name not in cfg.allowed_tools:
                continue
            catalog.append({
                "type": "tool",
                "name": tool_name,
                "description": tool.description,
            })

        # Skills
        for manifest in list_manifests():
            name = manifest.name
            if cfg.allowed_skills is not None and name not in cfg.allowed_skills:
                continue
            handler = get_handler(name)
            if handler is None:
                continue
            catalog.append({
                "type": "skill",
                "name": name,
                "description": manifest.description or "",
                "inputs": {k: str(v) for k, v in (manifest.inputs or {}).items()},
            })

        return catalog

    def _init_conversation(
        self, ctx: AgentContext, catalog: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Build the initial LLM conversation with system prompt and context."""
        cfg = self.config

        system = f"""{cfg.system_prompt}

You are an AI agent named {self.agent_name}. You have access to these tools and skills:

{json.dumps(catalog, indent=2)}

At each step, respond with a JSON object. You MUST choose ONE of:
1. Call a tool: {{"thought": "...", "tool": "<name>", "inputs": {{...}}}}
2. Call a skill: {{"thought": "...", "skill": "<name>", "inputs": {{...}}}}
3. Finalize: {{"thought": "...", "finalize": true, "outputs": {{...}}}}

Rules:
- Always include a "thought" explaining your reasoning.
- Budget remaining: ${cfg.tool_budget_usd:.2f}. Max steps: {cfg.max_steps}.
- Finalize when you have produced satisfactory outputs or exhausted options.
- ALWAYS respond with valid JSON. No markdown, no prose."""

        brand_ctx = ctx.state.get("brand_context", {})
        user_msg = json.dumps({
            "task": {
                "brand": brand_ctx.get("name", ""),
                "category": brand_ctx.get("category", ""),
                "positioning": brand_ctx.get("positioning", ""),
                "voice": brand_ctx.get("voice_attributes", []),
                "design_school": ctx.state.get("design_school", ""),
                "strategy": ctx.state.get("strategy", {}),
            },
            "extra": ctx.extra,
        })

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]

    async def _invoke_skill(
        self,
        ctx: AgentContext,
        skill_name: str,
        inputs: dict[str, Any],
        step_idx: int,
    ) -> dict[str, Any]:
        """Invoke a skill handler and return a summary dict."""
        from helix.core.db import session_factory
        from helix.skills.base import SkillContext
        from helix.skills.learning import format_learnings_preamble, load_learnings

        handler = get_handler(skill_name)
        if handler is None:
            return {"ok": False, "error": f"skill not found: {skill_name}", "cost_usd": 0.0}

        started = time.time()
        async with session_factory() as sess:
            learning_rows = await load_learnings(sess, skill_name=skill_name, brand_id=ctx.brand_id)
            preamble = format_learnings_preamble(learning_rows)

            skill_ctx = SkillContext(
                db=sess,
                brand_id=ctx.brand_id,
                workflow_run_id=ctx.run_id,
                task_id=None,
                workspace_id=ctx.workspace_id,
                brand_context=ctx.state.get("brand_context", {}),
                inputs=inputs,
                learnings=[preamble] if preamble else [],
            )

            try:
                result = await handler(skill_ctx)
            except Exception as exc:
                log.exception("agentic.skill_failed", skill=skill_name)
                result = SkillResult(ok=False, error=f"{type(exc).__name__}: {exc}")

        duration_ms = int((time.time() - started) * 1000)

        await emit_event(
            run_id=ctx.run_id,
            kind="agent.skill_call",
            payload={
                "agent": self.agent_name,
                "skill": skill_name,
                "step": step_idx,
                "ok": result.ok,
                "cost_usd": result.cost_usd,
                "duration_ms": duration_ms,
            },
        )

        return {
            "ok": result.ok,
            "summary": result.outputs.get("summary", "") if result.outputs else "",
            "cost_usd": result.cost_usd or 0.0,
            "duration_ms": duration_ms,
            "skill_result": result,
        }

    async def _invoke_tool(
        self,
        ctx: AgentContext,
        tool_name: str,
        inputs: dict[str, Any],
        step_idx: int,
    ) -> dict[str, Any]:
        """Invoke a tool and return a summary dict."""
        tool = get_tool(tool_name)
        if tool is None:
            return {"ok": False, "error": f"tool not found: {tool_name}", "cost_usd": 0.0}

        started = time.time()
        result = await tool.call(
            trace_id=ctx.state.get("langfuse_trace_id"),
            **inputs,
        )
        duration_ms = int((time.time() - started) * 1000)

        await emit_event(
            run_id=ctx.run_id,
            kind="agent.tool_call",
            payload={
                "agent": self.agent_name,
                "tool": tool_name,
                "step": step_idx,
                "ok": result.ok,
                "cost_usd": result.cost_usd,
                "duration_ms": duration_ms,
            },
        )

        # Truncate data for conversation context
        data_summary = str(result.data)[:1000] if result.data else ""

        return {
            "ok": result.ok,
            "summary": data_summary,
            "cost_usd": result.cost_usd or 0.0,
            "duration_ms": duration_ms,
            "error": result.error,
        }
