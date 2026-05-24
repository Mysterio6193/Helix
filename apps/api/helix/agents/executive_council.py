"""ExecutiveCouncilAgent — multi-agent boardroom debate loop."""
from __future__ import annotations

import json

from helix.agents.base import Agent, AgentContext, AgentResult
from helix.core.logging import get_logger
from helix.tools.registry import get_tool
from helix.workflows.helpers import emit_event

log = get_logger(__name__)

class ExecutiveCouncilAgent(Agent):
    name = "executive_council"
    description = "Simulates a boardroom debate between CMO, Creative Director, Media Buyer, and Copywriter."

    async def run(self, ctx: AgentContext) -> AgentResult:
        # 1. Fetch LLM tool
        llm = get_tool("openai_chat")
        if not llm:
            return AgentResult(ok=False, error="LLM tool 'openai_chat' not found.")

        # 2. Get event or task context
        event_name = ctx.state.get("event", "campaign_init")
        brand_ctx = ctx.state.get("brand_context", {})
        brand_name = brand_ctx.get("name", "Unknown Brand")
        
        await emit_event(
            run_id=ctx.run_id,
            kind="boardroom.start",
            payload={
                "event": event_name,
                "brand": brand_name,
                "msg": f"Initiating Executive Boardroom Council debate for brand '{brand_name}' due to event '{event_name}'."
            }
        )

        # 3. Setup Agent personas and debate conversation
        personas = {
            "media_buyer": """You are the AI Media Buyer for Helix OS. 
Your objective is budget efficiency, targeting, and monitoring metrics (ROAS, CTR, CAC).
You analyze performance events and frame the strategic goals of the campaign.
Keep your responses sharp, numerical, and execution-focused.""",
            
            "copywriter": """You are the AI Copywriter for Helix OS.
Your objective is generating high-converting marketing hooks, taglines, headlines, and call-to-actions.
You base your copy on the brand voice guidelines and media buyer's targeting.
Generate exactly 3 specific hook options during your turn and refine them as the debate progresses.""",
            
            "creative_director": """You are the AI Creative Director for Helix OS.
Your objective is visual aesthetics, design school compliance, and visual hierarchy.
You must choose a visual school (Minimal, Brutalist, Editorial) and pick visual style guides.
You criticize visual choices and align layouts to brand guidelines. Make sure Helix can render these visual schemas cleanly.""",
            
            "critic": """You are the AI Critic for Helix OS.
Your objective is compliance, edge-case detection, brand-alignment, and risk analysis.
You teardown the proposed copy hooks and visual directions, suggesting revisions to eliminate generic writing, poor layouts, or high-risk claims.""",
            
            "cmo": """You are the AI Chief Marketing Officer (CMO) for Helix OS.
Your objective is high-level orchestration, campaign alignment, revenue optimization, and final sign-off.
You summarize the boardroom discussion, open a formal voting round, resolve any ties, and synthesize the finalized plan."""
        }

        # 4. Formulate the starting context
        debate_history = [
            {
                "role": "system",
                "content": f"""You are simulating a marketing board meeting for brand '{brand_name}' ({brand_ctx.get('category', 'restaurant')}).
Active Event: '{event_name}'
Brand Vibe: {brand_ctx.get('vibe', 'warm-confident')}
Current Design School: {ctx.state.get('design_school', 'minimal')}

The boardroom consists of 5 members: Media Buyer, Copywriter, Creative Director, Critic, and CMO.
The boardroom must collaborate to refine:
1. One finalized visual design school selection (Brutalist, Editorial, Minimal).
2. The core target audience hook.
3. Three specific refined ad/creative copy hooks.
4. Budget and channel recommendations."""
            },
            {
                "role": "user",
                "content": f"The meeting has officially started. Let's begin the debate. Active event: {event_name}. Brand details: {json.dumps(brand_ctx, indent=2)}."
            }
        ]

        turns = ["media_buyer", "copywriter", "creative_director", "critic", "cmo"]
        debate_steps = []

        # Run 1 full debate cycle
        for role in turns:
            system_prompt = f"{personas[role]}\n\nRespond ONLY as this persona. Do not speak for other personas. Be highly contextual and refer directly to previous points made in the debate. Keep your reply under 250 words."
            
            # Send current debate history with role-specific system prompt
            messages = [{"role": "system", "content": system_prompt}] + [
                m for m in debate_history if m["role"] != "system"
            ]

            result = await llm.call(
                trace_id=ctx.state.get("langfuse_trace_id"),
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=1000,
            )

            if not result.ok:
                log.warning("boardroom.turn_failed", role=role, error=result.error)
                continue

            message_content = str(result.data).strip()
            
            # Append to debate history so subsequent turns can see it
            debate_history.append({
                "role": "assistant",
                "name": role,
                "content": f"[{role.upper()}]: {message_content}"
            })

            # Emit boardroom message event for Next.js timeline
            await emit_event(
                run_id=ctx.run_id,
                kind="boardroom.message",
                payload={
                    "agent": "executive_council",
                    "role": role,
                    "message": message_content
                }
            )

            debate_steps.append({
                "role": role,
                "content": message_content
            })

        # 5. CMO finalizes the decision via structured JSON generation
        cmo_system_prompt = """You are the CMO finalizing the executive boardroom decisions.
Read the boardroom debate history and extract the final agreed-upon campaign details.
You MUST respond with a valid JSON object matching this schema exactly:
{
  "summary": "High-level CMO summary of the debate and alignment",
  "design_school": "brutalist" | "minimal" | "editorial",
  "target_audience": "Specific defined target demographic hook",
  "copy_hooks": [
     "Hook 1",
     "Hook 2",
     "Hook 3"
  ],
  "channel_recommendations": ["Meta Ads", "Google Ads", "TikTok Ads"],
  "budget_allocation": {
     "Meta Ads": 0.50,
     "TikTok Ads": 0.30,
     "Google Ads": 0.20
  },
  "cmo_sign_off": true
}
Do not include any prose, markdown block markup, or notes. Output only the JSON string."""

        cmo_messages = [
            {"role": "system", "content": cmo_system_prompt},
            {"role": "user", "content": "Analyze the debate history and output the final Campaign specification JSON. Debate history:\n" + "\n".join([m["content"] for m in debate_history if "content" in m])}
        ]

        cmo_result = await llm.call(
            trace_id=ctx.state.get("langfuse_trace_id"),
            messages=cmo_messages,
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=1500,
            json_mode=True,
        )

        if not cmo_result.ok:
            return AgentResult(ok=False, error=f"CMO final sign-off failed: {cmo_result.error}")

        try:
            cmo_decision = (
                cmo_result.data
                if isinstance(cmo_result.data, dict)
                else json.loads(str(cmo_result.data))
            )
        except (json.JSONDecodeError, TypeError):
            log.warning("boardroom.cmo_parse_failed", raw=str(cmo_result.data))
            return AgentResult(ok=False, error="Failed to parse CMO boardroom decision JSON.")

        # Enforce selected design school
        selected_school = cmo_decision.get("design_school", "minimal")

        await emit_event(
            run_id=ctx.run_id,
            kind="boardroom.consensus",
            payload={
                "agent": "executive_council",
                "summary": cmo_decision.get("summary"),
                "design_school": selected_school,
                "copy_hooks": cmo_decision.get("copy_hooks", []),
                "budget_allocation": cmo_decision.get("budget_allocation", {})
            }
        )

        return AgentResult(
            ok=True,
            patch={
                "boardroom_debate": debate_steps,
                "boardroom_decision": cmo_decision,
                "design_school": selected_school,
                "target_audience": cmo_decision.get("target_audience"),
                "copy_hooks": cmo_decision.get("copy_hooks", []),
            }
        )
