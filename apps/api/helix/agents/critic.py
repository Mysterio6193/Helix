"""CriticAgent — quality gate; provides structured feedback + accept/revise verdict using multi-modal ensemble."""
from __future__ import annotations

from helix.agents.base import Agent, AgentContext, AgentResult
from helix.critics.ensemble import score as ensemble_score


class CriticAgent(Agent):
    name = "critic"
    description = "Critiques outputs against brand brief + visual school; decides accept or revise."

    async def run(self, ctx: AgentContext) -> AgentResult:
        candidate = ctx.extra.get("candidate")

        # Run the multi-modal critique ensemble
        report = await ensemble_score(ctx.state, candidate)

        critique = {
            "verdict": report.verdict,
            "score": report.weighted_score,
            "dimension_scores": report.dimension_scores,
            "failing_dimensions": report.failing_dimensions,
            "feedback": report.feedback,
            "target_branch": "visuals" if any(d in ["palette", "clip", "contrast"] for d in report.failing_dimensions) else "copy",
        }

        return AgentResult(
            ok=True,
            patch={"critiques": [critique]},  # operator.add reducer
            skill_results=[],
            error=None,
        )

