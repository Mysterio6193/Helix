"""BrandStrategistAgent — positioning, audience, voice."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class BrandStrategistAgent(Agent):
    name = "brand_strategist"
    description = "Develops positioning, audience, voice. Owns strategic brief."

    async def run(self, ctx: AgentContext) -> AgentResult:
        # Skill: brand_strategy_brief
        result = await self.invoke_skill(
            ctx,
            skill_name="brand_strategy_brief",
            inputs={
                "name": ctx.state.get("brand_context", {}).get("name") or ctx.state.get("brand_context", {}).get("brand", {}).get("name", ""),
                "category": ctx.state.get("inputs", {}).get("category", "restaurant"),
                "cuisine": ctx.state.get("inputs", {}).get("cuisine"),
                "city": ctx.state.get("inputs", {}).get("city"),
                "audience_hint": ctx.state.get("inputs", {}).get("audience"),
                "vibe": ctx.state.get("inputs", {}).get("vibe"),
            },
        )
        if not result.ok:
            return AgentResult(ok=False, error=result.error)
        return AgentResult(
            ok=True,
            patch={"strategy": result.outputs, "brief": result.outputs.get("brief", {})},
            skill_results=[result],
        )
