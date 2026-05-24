"""Manually trigger optimization evaluation for testing."""
import asyncio

from sqlalchemy import select

from helix.core.db import AsyncSessionLocal
from helix.intelligence.actions import ActionExecutor, ApprovalQueue
from helix.intelligence.rules_engine import RulesEngine
from helix.models.organization import Workspace


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Workspace).limit(1))
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            return

        
        engine = RulesEngine(session)
        triggered = await engine.evaluate_all_rules(workspace.id)
        
        
        for trigger in triggered:
            
            if trigger["approval_required"]:
                queue = ApprovalQueue(session)
                await queue.create_approval_request(
                    workspace.id,
                    trigger["rule_id"],
                    trigger["rule_name"],
                    trigger["actions"],
                    trigger["context"],
                )
            else:
                executor = ActionExecutor(session)
                results = await executor.execute_actions(
                    trigger["actions"],
                    workspace.id,
                    None,
                    trigger["context"],
                )
                for _r in results:
                    pass
        
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
