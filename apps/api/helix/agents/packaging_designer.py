"""PackagingDesignerAgent — dielines, label layouts, sticker packs."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class PackagingDesignerAgent(Agent):
    name = "packaging_designer"
    description = "Builds dielines + label artwork for cups, bags, boxes, stickers."

    async def run(self, ctx: AgentContext) -> AgentResult:
        sku = ctx.extra.get("sku", "cup_12oz")
        result = await self.invoke_skill(
            ctx,
            skill_name="design_packaging",
            inputs={
                "sku": sku,
                "strategy": ctx.state.get("strategy", {}),
                "design_system": ctx.state.get("design_system", {}),
                "copy": ctx.state.get("copy", {}),
                "logos": [v for v in ctx.state.get("visuals", []) if v.get("purpose") == "logo"],
            },
        )
        if not result.ok:
            return AgentResult(ok=False, error=result.error)
        return AgentResult(
            ok=True,
            patch={"visuals": result.outputs.get("visuals", [])},
            skill_results=[result],
            artifact_ids=[str(a) for a in result.asset_ids],
        )
