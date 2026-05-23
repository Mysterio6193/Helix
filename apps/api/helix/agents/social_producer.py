"""SocialProducerAgent — feed, reels, captions, schedule."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class SocialProducerAgent(Agent):
    name = "social_producer"
    description = "Produces social pack (IG/TikTok): images, captions, hashtags, schedule."

    async def run(self, ctx: AgentContext) -> AgentResult:
        result = await self.invoke_skill(
            ctx,
            skill_name="build_social_pack",
            inputs={
                "strategy": ctx.state.get("strategy", {}),
                "copy": ctx.state.get("copy", {}),
                "design_system": ctx.state.get("design_system", {}),
                "platforms": ctx.extra.get("platforms", ["instagram", "tiktok"]),
                "post_count": ctx.extra.get("post_count", 9),
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
                    "social_pack": result.outputs.get("plan", {}),
                },
            },
            skill_results=[result],
            artifact_ids=[str(a) for a in result.asset_ids],
        )
