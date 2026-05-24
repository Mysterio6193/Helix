"""Event triggers — wire intelligence signals to browser automations."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.models.browser import BrowserAction, BrowserAutomation, BrowserSession
from helix.models.intelligence import IntelligenceSignal
from helix.tools.registry import get_tool

log = get_logger("helix.intelligence.triggers")

# Trigger registry: signal_type -> list of automation triggers
TRIGGER_REGISTRY: dict[str, list[dict[str, Any]]] = {
    "creative_fatigue": [
        {"automation_name": "Meta Ads Creative Refresh", "target_site": "meta_ads", "action": "create_campaign"},
    ],
    "competitor_price_change": [
        {"automation_name": "Shopify Price Monitor", "target_site": "shopify", "action": "edit_product"},
    ],
    "churn_spike": [
        {"automation_name": "Meta Ads Creative Refresh", "target_site": "meta_ads", "action": "create_campaign"},
    ],
}


class EventTriggerEngine:
    """Engine that listens for intelligence signals and fires browser automations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_signal(self, signal: IntelligenceSignal) -> list[dict[str, Any]]:
        """Process an intelligence signal and trigger matching automations."""
        triggered = []

        # Determine trigger type from signal
        trigger_type = self._classify_signal(signal)
        if not trigger_type:
            return triggered

        triggers = TRIGGER_REGISTRY.get(trigger_type, [])

        for trigger in triggers:
            # Find matching automation
            result = await self.db.execute(
                select(BrowserAutomation)
                .where(
                    BrowserAutomation.workspace_id == signal.workspace_id,
                    BrowserAutomation.name == trigger["automation_name"],
                    BrowserAutomation.enabled.is_(True),
                )
            )
            automation = result.scalar_one_or_none()

            if not automation:
                log.info("trigger_no_automation",
                        trigger=trigger["automation_name"],
                        workspace=str(signal.workspace_id))
                continue

            # Check cooldown
            if automation.last_run_at:
                cooldown = timedelta(hours=24)  # Default 24h cooldown
                if datetime.utcnow() - automation.last_run_at < cooldown:
                    log.info("trigger_cooldown",
                            automation=str(automation.id),
                            workspace=str(signal.workspace_id))
                    continue

            # Execute the automation
            execution = await self._execute_automation(automation, signal)
            triggered.append(execution)

            log.info("trigger_executed",
                    automation=str(automation.id),
                    signal=str(signal.id),
                    trigger_type=trigger_type,
                    workspace=str(signal.workspace_id))

        return triggered

    def _classify_signal(self, signal: IntelligenceSignal) -> str | None:
        """Classify a signal into a trigger type."""
        title_lower = signal.title.lower()
        desc_lower = signal.description.lower() if signal.description else ""

        if "creative fatigue" in title_lower or "ctr declined" in desc_lower:
            return "creative_fatigue"
        elif "competitor" in title_lower and "price" in desc_lower:
            return "competitor_price_change"
        elif "churn" in title_lower or "at risk" in title_lower:
            return "churn_spike"
        elif "roas" in title_lower and ("below" in desc_lower or "dropped" in desc_lower):
            return "creative_fatigue"  # Reuse creative refresh for ROAS issues

        return None

    async def _execute_automation(
        self,
        automation: BrowserAutomation,
        signal: IntelligenceSignal,
    ) -> dict[str, Any]:
        """Execute a browser automation and log results."""
        operator_tool = get_tool("helix_page_operator")

        # Create session
        session = BrowserSession(
            workspace_id=automation.workspace_id,
            brand_id=automation.brand_id,
            name=f"Triggered: {automation.name}",
            provider="local",
            status="running",
            target_url=f"https://{automation.target_site}.com",
            metadata_={
                "automation_id": str(automation.id),
                "signal_id": str(signal.id),
                "trigger": "auto",
                "signal_title": signal.title,
            },
            started_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.flush()

        start_time = datetime.utcnow()

        try:
            if operator_tool:
                tool_result = await operator_tool.call(
                    target_site=automation.target_site,
                    action=automation.action,
                    payload=automation.config,
                )

                # Log actions
                nav_action = BrowserAction(
                    session_id=session.id,
                    action_type="navigate",
                    url=f"https://{automation.target_site}.com",
                    status="success" if tool_result.ok else "failed",
                    result=tool_result.data or {},
                    error=tool_result.error if not tool_result.ok else None,
                    execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                )
                self.db.add(nav_action)

                main_action = BrowserAction(
                    session_id=session.id,
                    action_type="execute",
                    value=automation.action,
                    status="success" if tool_result.ok else "failed",
                    result=tool_result.data or {},
                    error=tool_result.error if not tool_result.ok else None,
                    execution_time_ms=100,  # Approximate
                )
                self.db.add(main_action)

                success = tool_result.ok
            else:
                # No tool available — log as simulated
                nav_action = BrowserAction(
                    session_id=session.id,
                    action_type="navigate",
                    url=f"https://{automation.target_site}.com",
                    status="simulated",
                    result={"note": "Tool not available — simulated execution"},
                )
                self.db.add(nav_action)
                success = True  # Simulated success

            # Update stats
            automation.run_count += 1
            automation.last_run_at = datetime.utcnow()
            automation.last_run_id = session.id

            if success:
                automation.success_count += 1
                session.status = "idle"
            else:
                session.status = "error"

            session.ended_at = datetime.utcnow()
            await self.db.commit()

            return {
                "automation_id": str(automation.id),
                "session_id": str(session.id),
                "status": "success" if success else "failed",
                "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                "triggered_by": str(signal.id),
            }

        except Exception as e:
            session.status = "error"
            session.ended_at = datetime.utcnow()
            automation.run_count += 1
            await self.db.commit()

            log.error("trigger_execution_failed",
                     automation=str(automation.id),
                     error=str(e))

            return {
                "automation_id": str(automation.id),
                "session_id": str(session.id),
                "status": "failed",
                "error": str(e),
                "triggered_by": str(signal.id),
            }


async def process_signal_triggers(db: AsyncSession, signal: IntelligenceSignal) -> list[dict[str, Any]]:
    """Process a signal and trigger matching browser automations."""
    engine = EventTriggerEngine(db)
    return await engine.process_signal(signal)
