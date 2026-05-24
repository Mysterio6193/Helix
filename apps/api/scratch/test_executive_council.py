import asyncio
import uuid
from typing import Any

from helix.agents.base import AgentContext
from helix.agents.executive_council import ExecutiveCouncilAgent
from helix.tools.base import Tool, ToolResult
from helix.tools.registry import register_tool


# Register a mock openai_chat tool so we can test the debate logic deterministically without API keys
class MockOpenAIChat(Tool):
    name = "openai_chat"
    description = "Mock OpenAI Chat tool for testing."

    async def _call(self, messages: list[dict[str, Any]], **kwargs) -> ToolResult:
        # Determine which agent is calling by looking at the system prompt
        system_content = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        
        if "CMO" in system_content:
            data = {
                "summary": "The council has successfully aligned on a bold campaign targeting health-conscious professionals.",
                "design_school": "editorial",
                "target_audience": "Health-conscious urban professionals",
                "copy_hooks": [
                    "Fuel your day with organic goodness",
                    "Eat clean, live vibrant",
                    "Pure nutrition delivered straight to your door"
                ],
                "channel_recommendations": ["Meta Ads", "Google Ads"],
                "budget_allocation": {
                    "Meta Ads": 0.60,
                    "Google Ads": 0.40
                },
                "cmo_sign_off": True
            }
            return ToolResult(ok=True, data=data, cost_usd=0.005)
        elif "Media Buyer" in system_content:
            return ToolResult(ok=True, data="We need to maximize ROAS by targeting local professionals aged 25-45. I recommend shifting 60% of budget to Meta Ads due to high visual CTR.", cost_usd=0.001)
        elif "Copywriter" in system_content:
            return ToolResult(ok=True, data="Here are 3 hook ideas:\n1. Organic fuel for busy people.\n2. Freshly picked. Fast delivery.\n3. The clean eating revolution is here.", cost_usd=0.001)
        elif "Creative Director" in system_content:
            return ToolResult(ok=True, data="An editorial visual school aligns perfectly with a premium food brand. We should use high-contrast serif typography and rich organic tones.", cost_usd=0.001)
        elif "Critic" in system_content:
            return ToolResult(ok=True, data="The proposed hooks are slightly generic. Let's make sure the copy highlights 'delivery straight to your door' to increase conversion.", cost_usd=0.001)
        
        return ToolResult(ok=True, data="Mock response", cost_usd=0.001)

register_tool(MockOpenAIChat())

# Mock helix.events.bus.publish to prevent connection to a running redis server in tests
import helix.events.bus
import helix.workflows.helpers


async def mock_publish(db, *, kind, channel, payload, **kwargs):
    pass
helix.events.bus.publish = mock_publish
helix.workflows.helpers.publish = mock_publish

async def main():
    agent = ExecutiveCouncilAgent()
    
    brand_ctx = {
        "name": "Greens & Grains",
        "category": "Healthy Fast Casual",
        "vibe": "organic, sophisticated, fresh",
        "voice_attributes": ["warm", "confident", "healthy"]
    }
    
    ctx = AgentContext(
        state={
            "brand_id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "run_id": str(uuid.uuid4()),
            "brand_context": brand_ctx,
            "event": "roas_dropped",
            "design_school": "minimal",
            "langfuse_trace_id": "test_trace_123"
        }
    )
    
    result = await agent.run(ctx)
    
    if result.ok:
        patch = result.patch
        patch.get("boardroom_decision", {})
        for _hook in patch.get("copy_hooks", []):
            pass
        for _step in patch.get("boardroom_debate", []):
            pass
    else:
        pass

if __name__ == "__main__":
    asyncio.run(main())
