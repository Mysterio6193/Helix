"""LaunchManagerAgent — coordinates multi-channel launch campaigns."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class LaunchManagerAgent(Agent):
    name = "launch_manager"
    description = (
        "Coordinates a launch campaign: schedule, email drafts (via Gmail draft), "
        "social calendar, press kit, Notion campaign board."
    )

    async def run(self, ctx: AgentContext) -> AgentResult:
        result = await self.invoke_skill(
            ctx,
            skill_name="orchestrate_launch_campaign",
            inputs={
                "strategy": ctx.state.get("strategy", {}),
                "copy": ctx.state.get("copy", {}),
                "design_system": ctx.state.get("design_system", {}),
                "channels": ctx.extra.get("channels", ["email", "social", "press"]),
                "launch_date": ctx.state.get("inputs", {}).get("launch_date"),
                "notion_database_id": ctx.state.get("inputs", {}).get("notion_database_id"),
            },
        )
        if not result.ok:
            return AgentResult(ok=False, error=result.error)
        return AgentResult(
            ok=True,
            patch={
                "output": {
                    **ctx.state.get("output", {}),
                    "launch_campaign": result.outputs,
                }
            },
            skill_results=[result],
            artifact_ids=[str(a) for a in result.asset_ids],
        )
