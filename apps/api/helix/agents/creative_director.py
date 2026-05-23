"""CreativeDirectorAgent — picks design school, sets art direction."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class CreativeDirectorAgent(Agent):
    name = "creative_director"
    description = "Selects one of the 5 visual schools, locks art direction tokens."

    async def run(self, ctx: AgentContext) -> AgentResult:
        system_prompt = f"""You are the Creative Director Agent for Helix. Your goal is to select the perfect design school and visual direction for the brand.

Your primary skill is: 'select_design_school'

Please call this skill first to choose the appropriate design school. You should pass inputs like:
{{
  "strategy": <strategy from task>,
  "brief": <brief from task>,
  "user_pref_school": "{ctx.state.get("inputs", {}).get("preferred_school", "")}"
}}

After getting the result, finalize by calling 'finalize' with:
{{
  "design_school": <the selected school string, e.g. "modern-minimal">,
  "design_system": <the design system tokens dictionary>
}}
"""

        return await self.run_agentic(
            ctx,
            system_prompt=system_prompt,
            allowed_skills=["select_design_school"],
            allowed_tools=["openai_chat"],
            max_steps=3,
            tool_budget_usd=1.00,
        )

