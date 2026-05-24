"""Agent Swarm Orchestration — Dynamic multi-agent task decomposition and execution.

Enables:
- Hierarchical task planning (swarm leader → sub-agents)
- Dynamic agent creation for specialized tasks
- Parallel execution with result aggregation
- Agent-to-agent communication
- Consensus building for complex decisions
"""
from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from helix.core.cache import get_cache
from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.llm.gateway import complete

log = get_logger("helix.swarm")
settings = get_settings()


@dataclass
class Task:
    """A unit of work for the swarm."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    agent_type: str = "general"
    dependencies: list[str] = field(default_factory=list)
    priority: int = 5  # 1-10, lower is more urgent
    context: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    status: str = "pending"  # pending, running, completed, failed
    error: str | None = None


@dataclass
class SwarmPlan:
    """A decomposition of a complex goal into tasks."""
    goal: str = ""
    tasks: list[Task] = field(default_factory=list)
    estimated_duration: int = 0  # seconds
    required_agents: list[str] = field(default_factory=list)


class SwarmPlanner:
    """Breaks complex goals into executable task plans."""

    async def plan(self, goal: str, context: dict[str, Any] | None = None) -> SwarmPlan:
        """Decompose a goal into a task plan using an LLM."""
        system_prompt = """You are a master project planner for an AI creative operating system.
Given a goal, break it down into specific, actionable tasks.

Return a JSON object:
{
  "tasks": [
    {
      "description": "specific task description",
      "agent_type": "copywriter|visual_designer|web_builder|social_producer|analyst|researcher|general",
      "dependencies": ["task_id_or_empty"],
      "priority": 1-10
    }
  ],
  "estimated_duration": estimated_seconds,
  "required_agents": ["agent_type_1", "agent_type_2"]
}

Rules:
- Each task should be completable in under 5 minutes
- Tasks with dependencies must list prerequisite task indices (0-based)
- Prioritize tasks that unblock others (lower priority number = more urgent)
- Include a "synthesize" task at the end to combine results"""

        ctx = f"\nContext: {json.dumps(context, default=str)}" if context else ""
        prompt = f"Goal: {goal}{ctx}\n\nBreak this down into tasks."

        try:
            result = await complete(
                model="openai:gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                system=system_prompt,
                temperature=0.3,
                json_mode=True,
            )
            plan_data = json.loads(result.text)

            tasks = []
            for i, t in enumerate(plan_data.get("tasks", [])):
                task = Task(
                    id=str(i),
                    description=t["description"],
                    agent_type=t.get("agent_type", "general"),
                    dependencies=[str(d) for d in t.get("dependencies", [])],
                    priority=t.get("priority", 5),
                    context=context or {},
                )
                tasks.append(task)

            return SwarmPlan(
                goal=goal,
                tasks=tasks,
                estimated_duration=plan_data.get("estimated_duration", 300),
                required_agents=plan_data.get("required_agents", []),
            )
        except Exception:
            log.exception("swarm_planning_failed")
            # Fallback: single task
            return SwarmPlan(
                goal=goal,
                tasks=[Task(description=goal, agent_type="general")],
            )


class AgentSwarm:
    """Orchestrates multiple agents to complete complex tasks."""

    def __init__(self, max_concurrent: int = 5) -> None:
        self.max_concurrent = max_concurrent
        self.cache = get_cache()
        self.planner = SwarmPlanner()

    async def execute(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
        max_iterations: int = 10,
    ) -> dict[str, Any]:
        """Execute a goal using the swarm.

        1. Plan: Decompose goal into tasks
        2. Schedule: Execute tasks respecting dependencies
        3. Synthesize: Combine results into final output
        """
        log.info("swarm.execute_start", goal=goal)

        # Step 1: Plan
        plan = await self.planner.plan(goal, context)
        log.info("swarm.plan_complete", tasks=len(plan.tasks), agents=plan.required_agents)

        # Step 2: Execute with dependency resolution
        completed: dict[str, Task] = {}
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_task(task: Task) -> None:
            async with semaphore:
                task.status = "running"
                log.info("swarm.task_start", task_id=task.id, agent=task.agent_type)

                try:
                    # Gather dependency results
                    dep_results = {
                        dep: completed[dep].result
                        for dep in task.dependencies
                        if dep in completed
                    }

                    # Execute based on agent type
                    result = await self._execute_with_agent(
                        task.agent_type,
                        task.description,
                        {**task.context, "dependencies": dep_results},
                    )

                    task.result = result
                    task.status = "completed"
                    log.info("swarm.task_complete", task_id=task.id)

                except Exception as exc:
                    task.status = "failed"
                    task.error = str(exc)
                    log.error("swarm.task_failed", task_id=task.id, error=str(exc))

        # Execute tasks in waves (respecting dependencies)
        remaining = list(plan.tasks)
        iterations = 0

        while remaining and iterations < max_iterations:
            iterations += 1
            ready = [
                t for t in remaining
                if all(dep in completed for dep in t.dependencies)
            ]

            if not ready:
                # Deadlock detected
                log.error("swarm.deadlock_detected", remaining=[t.id for t in remaining])
                break

            # Execute ready tasks in parallel
            tasks = [execute_task(t) for t in ready]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Move completed tasks from remaining
            for t in ready:
                if t.status in ("completed", "failed"):
                    completed[t.id] = t
                    remaining.remove(t)

        # Step 3: Synthesize results
        synthesis = await self._synthesize_results(plan.goal, list(completed.values()))

        return {
            "success": all(t.status == "completed" for t in completed.values()),
            "goal": goal,
            "plan": plan,
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status,
                    "result": t.result,
                    "error": t.error,
                }
                for t in completed.values()
            ],
            "synthesis": synthesis,
            "duration_seconds": plan.estimated_duration,
        }

    async def _execute_with_agent(
        self,
        agent_type: str,
        task: str,
        context: dict[str, Any],
    ) -> Any:
        """Execute a task using the appropriate agent."""
        agent_prompts = {
            "copywriter": "You are an expert copywriter. Create compelling, on-brand copy.",
            "visual_designer": "You are a visual designer. Describe designs, concepts, and creative directions.",
            "web_builder": "You are a web developer. Generate code, components, and technical solutions.",
            "social_producer": "You are a social media manager. Create engaging social content.",
            "analyst": "You are a data analyst. Analyze metrics, trends, and provide insights.",
            "researcher": "You are a market researcher. Gather insights, competitive analysis, and trends.",
            "general": "You are a versatile AI assistant. Complete the task efficiently.",
        }

        system = agent_prompts.get(agent_type, agent_prompts["general"])
        ctx = f"\nContext: {json.dumps(context, default=str)}" if context else ""

        result = await complete(
            model="openai:gpt-4o",
            messages=[{"role": "user", "content": f"Task: {task}{ctx}"}],
            system=system,
            temperature=0.7,
        )

        return {
            "text": result.text,
            "model": result.model,
            "cost_usd": result.cost_usd,
        }

    async def _synthesize_results(self, goal: str, tasks: list[Task]) -> dict[str, Any]:
        """Combine task results into a coherent final output."""
        results_text = "\n\n".join([
            f"Task {t.id} ({t.agent_type}):\n{t.result.get('text', str(t.result))}"
            for t in tasks
            if t.result
        ])

        synthesis_prompt = f"""Original Goal: {goal}

Individual Task Results:
{results_text}

Synthesize these results into a cohesive final deliverable. Identify conflicts, reinforce themes, and create a unified output. Return structured JSON with:
- summary: executive summary
- deliverables: list of final outputs
- recommendations: next steps
- conflicts: any contradictions found"""

        try:
            result = await complete(
                model="openai:gpt-4o",
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=0.5,
                json_mode=True,
            )
            return json.loads(result.text)
        except Exception as exc:
            log.exception("swarm.synthesis_failed")
            return {"summary": "Synthesis failed", "error": str(exc)}

    async def brainstorm(
        self,
        topic: str,
        num_agents: int = 5,
        rounds: int = 3,
    ) -> dict[str, Any]:
        """Run a brainstorming session with multiple AI agents.

        Each agent generates ideas, then they build on each other's ideas.
        """
        agents = [
            "creative_director",
            "copywriter",
            "brand_strategist",
            "social_producer",
            "analyst",
        ][:num_agents]

        all_ideas: list[dict[str, Any]] = []

        for round_num in range(rounds):
            log.info("swarm.brainstorm_round", round=round_num + 1)
            round_ideas: list[dict[str, Any]] = []

            for agent_type in agents:
                prompt = f"""Topic: {topic}
Round: {round_num + 1}/{rounds}

Previous ideas: {json.dumps([i['idea'] for i in all_ideas], indent=2)}

As a {agent_type}, generate 3 unique, creative ideas.
Consider: feasibility, impact, brand alignment, and novelty."""

                result = await complete(
                    model="openai:gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9,
                )

                round_ideas.append({
                    "agent": agent_type,
                    "round": round_num + 1,
                    "idea": result.text,
                })

            all_ideas.extend(round_ideas)

        # Rank and filter best ideas
        ranking_prompt = f"""Rank these ideas for: {topic}

Ideas:
{json.dumps(all_ideas, indent=2)}

Return top 5 ideas with reasoning for each."""

        ranking = await complete(
            model="openai:gpt-4o",
            messages=[{"role": "user", "content": ranking_prompt}],
            temperature=0.3,
        )

        return {
            "topic": topic,
            "rounds": rounds,
            "agents": agents,
            "all_ideas": all_ideas,
            "top_ideas": ranking.text,
            "total_ideas": len(all_ideas),
        }


# Global swarm instance
_swarm: AgentSwarm | None = None


def get_swarm() -> AgentSwarm:
    global _swarm
    if _swarm is None:
        _swarm = AgentSwarm()
    return _swarm
