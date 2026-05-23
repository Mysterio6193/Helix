"""OrchestratorAgent — top-level coordinator that routes the workflow plan."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult
from helix.workflows.helpers import emit_event


class OrchestratorAgent(Agent):
    name = "orchestrator"
    description = "Routes workflows: loads brand context, picks slice plan, hands off to specialists."

    async def run(self, ctx: AgentContext) -> AgentResult:
        workflow = ctx.state.get("workflow", "")
        await emit_event(
            run_id=ctx.run_id,
            kind="orchestrator.start",
            payload={"workflow": workflow, "inputs_keys": list(ctx.state.get("inputs", {}).keys())},
        )
        # Brand context preload happens in workflow node before us; orchestrator may
        # apply config defaults or pick a slice variant here.
        return AgentResult(
            ok=True,
            patch={
                "plan": [
                    {"step": s, "status": "pending"}
                    for s in ctx.state.get("config", {}).get("plan", [])
                ]
            },
        )
