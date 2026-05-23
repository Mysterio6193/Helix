"""VisualDesignerAgent — logos, posters, photo direction, hero imagery."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class VisualDesignerAgent(Agent):
    name = "visual_designer"
    description = "Generates logos, posters, hero images using design-system tokens."

    async def run(self, ctx: AgentContext) -> AgentResult:
        purpose = ctx.extra.get("purpose", "logo")
        skill_by_purpose = {
            "logo": "design_logo",
            "wordmark": "design_wordmark",
            "poster": "design_poster",
            "hero": "design_hero_image",
            "social_image": "design_social_image",
        }
        skill_name = skill_by_purpose.get(purpose, "design_logo")

        system_prompt = f"""You are the Visual Designer Agent for Helix. Your goal is to generate outstanding visual brand assets for the brand.
The user wants to generate a visual for the purpose: '{purpose}'.

Your primary skill to call first is: '{skill_name}'

Please call this skill first to establish the base design variants. You should pass inputs like:
{{
  "strategy": <strategy from task>,
  "brief": <brief from task>,
  "design_system": <design_system from task>,
  "design_school": <design_school from task>,
  "variant_count": {ctx.extra.get("variant_count", 4)}
}}

After invoking the skill and observing the generated asset(s), if they are excellent, finalize. If you want to refine or generate more variants using specific models, you may call tools like 'flux_image', 'openai_image', or 'sdxl_image'.
Once you are done, call 'finalize' with a dict containing "visuals" (a list of generated visual dicts/objects) in the "outputs" parameter.
"""

        return await self.run_agentic(
            ctx,
            system_prompt=system_prompt,
            allowed_skills=["design_logo", "design_wordmark", "design_poster", "design_hero_image", "design_social_image"],
            allowed_tools=["openai_chat", "openai_image", "flux_image", "flux_schnell", "sdxl_image"],
            max_steps=5,
            tool_budget_usd=2.00,
        )

