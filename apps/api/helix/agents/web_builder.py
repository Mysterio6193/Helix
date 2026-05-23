"""WebBuilderAgent — scaffolds restaurant websites and deploys to Vercel."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class WebBuilderAgent(Agent):
    name = "web_builder"
    description = "Scaffolds a Next.js restaurant site, pushes to GitHub, deploys via Vercel."

    async def run(self, ctx: AgentContext) -> AgentResult:
        system_prompt = f"""You are the Web Builder Agent for Helix. Your goal is to build and deploy an exquisite restaurant website.

Your primary skill is: 'build_restaurant_site'

Please call this skill first to generate the website layout and configuration. You should pass inputs like:
{{
  "strategy": <strategy from task>,
  "copy": <copy from task>,
  "design_system": <design_system from task>,
  "visuals": <visuals from task>,
  "domain_hint": "{ctx.state.get("inputs", {}).get("domain_hint", "")}",
  "deploy": {ctx.extra.get("deploy", True)}
}}

After getting the result, you can do any final validation. Finalize by calling 'finalize' with:
{{
  "output": {{
     "website": <the website object returned from the skill>
  }}
}}
"""

        return await self.run_agentic(
            ctx,
            system_prompt=system_prompt,
            allowed_skills=["build_restaurant_site"],
            allowed_tools=["openai_chat", "vercel_deploy"],
            max_steps=3,
            tool_budget_usd=2.00,
        )

