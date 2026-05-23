"""MenuDesignerAgent — structured menu copy + photography brief + mockups."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class MenuDesignerAgent(Agent):
    name = "menu_designer"
    description = "Produces a printable menu pack: section structure, dish copy, photography brief, mockups."

    async def run(self, ctx: AgentContext) -> AgentResult:
        result = await self.invoke_skill(
            ctx,
            skill_name="design_menu_pack",
            inputs={
                "strategy": ctx.state.get("strategy", {}),
                "copy": ctx.state.get("copy", {}),
                "design_system": ctx.state.get("design_system", {}),
                "design_school": ctx.state.get("design_school"),
                "cuisine": ctx.extra.get("cuisine"),
                "format": ctx.extra.get("format", "a4_portrait"),
                "mockup_count": ctx.extra.get("mockup_count", 3),
            },
        )
        if not result.ok:
            return AgentResult(ok=False, error=result.error)
        return AgentResult(
            ok=True,
            patch={
                "visuals": result.outputs.get("visuals", []),
                "output": {
                    **ctx.state.get("output", {}),
                    "menu_pack": result.outputs.get("menu", {}),
                },
            },
            skill_results=[result],
            artifact_ids=[str(a) for a in result.asset_ids],
        )
