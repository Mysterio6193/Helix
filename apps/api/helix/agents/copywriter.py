"""CopywriterAgent — taglines, headlines, body copy, captions."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult


class CopywriterAgent(Agent):
    name = "copywriter"
    description = "Generates taglines, headlines, body, captions, microcopy."

    async def run(self, ctx: AgentContext) -> AgentResult:
        purpose = ctx.extra.get("purpose", "taglines")
        skill_by_purpose = {
            "taglines": "generate_taglines",
            "headlines": "generate_headlines",
            "body": "generate_body_copy",
            "captions": "generate_social_captions",
            "menu_copy": "generate_menu_descriptions",
        }
        skill_name = skill_by_purpose.get(purpose, "generate_taglines")

        system_prompt = f"""You are the Copywriter Agent for Helix. Your goal is to generate outstanding brand copywriting.
The user wants to generate copy for the purpose: '{purpose}'.

Your primary skill to call first is: '{skill_name}'

Please call this skill first to establish the base copywriting drafts. You should pass inputs like:
{{
  "strategy": <strategy from task>,
  "brief": <brief from task>,
  "count": {ctx.extra.get("count", 5)},
  "tone": "{ctx.state.get("strategy", {}).get("voice", "warm-confident")}"
}}

After invoking the skill and observing the generated copy, if you want to refine it, you can call 'openai_chat' or 'web_search'.
Once you are done, call 'finalize' with a dict containing "copy" (a dict where '{purpose}' maps to your finalized copy result) in the "outputs" parameter, e.g.:
{{
  "copy": {{
     "{purpose}": <your_finalized_copy>
  }}
}}
"""

        return await self.run_agentic(
            ctx,
            system_prompt=system_prompt,
            allowed_skills=["generate_taglines", "generate_headlines", "generate_body_copy", "generate_social_captions", "generate_menu_descriptions"],
            allowed_tools=["openai_chat", "web_search"],
            max_steps=5,
            tool_budget_usd=1.00,
        )

