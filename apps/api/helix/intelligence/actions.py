"""Auto-actions executor — performs optimization actions autonomously."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.models.intelligence import IntelligenceSignal
from helix.tools.registry import get_tool

log = get_logger(__name__)


class ActionExecutor:
    """Execute optimization actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_actions(
        self,
        actions: list[dict[str, Any]],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute a list of actions and return results."""
        results = []

        for action in actions:
            try:
                result = await self._execute_single_action(action, workspace_id, brand_id, context)
                results.append(result)
            except Exception as e:
                log.error("action_execution_failed", action=action["type"], error=str(e))
                results.append({
                    "action": action["type"],
                    "status": "failed",
                    "error": str(e),
                })

        return results

    async def _execute_single_action(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single action."""
        action_type = action["type"]

        handlers = {
            "reduce_budget": self._reduce_budget,
            "pause_adset": self._pause_adset,
            "reallocate_budget": self._reallocate_budget,
            "scale_variant": self._scale_variant,
            "generate_variants": self._generate_variants,
            "launch_workflow": self._launch_workflow,
            "browser_automation": self._browser_automation,
            "generate_signal": self._generate_signal,
        }

        handler = handlers.get(action_type)
        if not handler:
            return {"action": action_type, "status": "unknown", "error": "Unknown action type"}

        return await handler(action, workspace_id, brand_id, context)

    async def _reduce_budget(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Reduce budget on underperforming ad set."""
        target = action.get("target", "worst_performing_adset")
        amount = action.get("amount", 0.3)

        # In production, this would call Meta Ads API
        # For now, simulate the action
        log.info("auto_reduce_budget", target=target, amount=amount, workspace=str(workspace_id))

        return {
            "action": "reduce_budget",
            "status": "simulated",
            "target": target,
            "reduction": f"{amount * 100}%",
            "note": "Integration with Meta Ads API required for live execution",
        }

    async def _pause_adset(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Pause a fatigued ad set."""
        target = action.get("target", "fatigued_adset")

        log.info("auto_pause_adset", target=target, workspace=str(workspace_id))

        return {
            "action": "pause_adset",
            "status": "simulated",
            "target": target,
            "note": "Integration with Meta Ads API required for live execution",
        }

    async def _reallocate_budget(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Reallocate budget between channels."""
        from_channel = action.get("from", "lowest_roas")
        to_channel = action.get("to", "highest_roas")
        amount = action.get("amount", 0.2)

        log.info("auto_reallocate_budget",
                from_channel=from_channel,
                to_channel=to_channel,
                amount=amount,
                workspace=str(workspace_id))

        return {
            "action": "reallocate_budget",
            "status": "simulated",
            "from": from_channel,
            "to": to_channel,
            "amount": f"{amount * 100}%",
            "note": "Integration with Meta Ads API required for live execution",
        }

    async def _scale_variant(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Scale a winning experiment variant."""
        action.get("target", "winner")
        amount = action.get("amount", 2.0)
        experiment_id = context.get("experiment_id")

        log.info("auto_scale_variant",
                experiment=experiment_id,
                multiplier=amount,
                workspace=str(workspace_id))

        return {
            "action": "scale_variant",
            "status": "simulated",
            "experiment_id": experiment_id,
            "multiplier": amount,
            "note": "Integration with Meta Ads API required for live execution",
        }

    async def _generate_variants(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate creative variants using image generation."""
        count = action.get("count", 3)
        style = action.get("style", "auto")

        from helix.llm.gateway import generate_image
        from helix.models.workflow import Asset

        # Build prompts based on context
        product = context.get("product_name", "product")
        campaign = context.get("campaign_name", "campaign")

        prompts = []
        for i in range(count):
            prompts.append(
                f"Professional advertising creative for {campaign}, "
                f"showcasing {product}, "
                f"{style} style, variant {i+1} of {count}, "
                f"high-end commercial photography, clean background, "
                f"optimized for social media ads, vibrant colors, sharp focus"
            )

        generated = []
        total_cost = 0.0

        try:
            for prompt in prompts:
                result = await generate_image(
                    prompt=prompt,
                    size="1024x1024",
                    quality="high",
                    n=1,
                    s3_prefix="generated/variants",
                )

                for img in result.images:
                    asset = Asset(
                        workspace_id=workspace_id,
                        brand_id=brand_id,
                        kind="image",
                        mime_type="image/png",
                        s3_key=img["s3_key"],
                        width=img.get("width"),
                        height=img.get("height"),
                        purpose="ad_creative",
                        metadata_={
                            "generated_by": "optimization_engine",
                            "style": style,
                            "prompt": prompt,
                            "model": result.model,
                            "context": context,
                        },
                    )
                    self.db.add(asset)
                    generated.append(img["s3_key"])

                total_cost += result.cost_usd or 0.0

            await self.db.commit()

            log.info("auto_generate_variants",
                    count=count,
                    style=style,
                    generated=len(generated),
                    cost=total_cost,
                    workspace=str(workspace_id))

            return {
                "action": "generate_variants",
                "status": "completed",
                "count": count,
                "style": style,
                "generated": len(generated),
                "assets": generated,
                "cost_usd": total_cost,
            }

        except Exception as e:
            log.error("auto_generate_variants_failed",
                     error=str(e),
                     workspace=str(workspace_id))
            return {
                "action": "generate_variants",
                "status": "failed",
                "count": count,
                "error": str(e),
            }

    async def _browser_automation(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a browser automation."""
        target_site = action.get("target_site", "meta_ads")
        site_action = action.get("action", "login")
        config = action.get("config", {})

        # Get the page operator tool
        operator_tool = get_tool("helix_page_operator")
        if not operator_tool:
            return {
                "action": "browser_automation",
                "status": "failed",
                "error": "Page operator tool not available",
            }

        try:
            tool_result = await operator_tool.call(
                target_site=target_site,
                action=site_action,
                payload=config,
            )

            log.info("auto_browser_automation",
                    site=target_site,
                    action=site_action,
                    workspace=str(workspace_id))

            return {
                "action": "browser_automation",
                "status": "success" if tool_result.ok else "failed",
                "site": target_site,
                "action_type": site_action,
                "result": tool_result.data if tool_result.ok else None,
                "error": tool_result.error if not tool_result.ok else None,
            }
        except Exception as e:
            return {
                "action": "browser_automation",
                "status": "failed",
                "error": str(e),
            }

    async def _launch_workflow(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Launch a workflow."""
        workflow = action.get("workflow", "winback_campaign")
        target = action.get("target", "at_risk_segment")

        log.info("auto_launch_workflow",
                workflow=workflow,
                target=target,
                workspace=str(workspace_id))

        return {
            "action": "launch_workflow",
            "status": "queued",
            "workflow": workflow,
            "target": target,
            "note": f"{workflow} workflow queued for execution",
        }

    async def _generate_signal(
        self,
        action: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate an intelligence signal."""
        layer = action.get("layer", "campaign")
        severity = action.get("severity", "info")
        title = action.get("title", "Auto-optimization executed")

        signal = IntelligenceSignal(
            workspace_id=workspace_id,
            brand_id=brand_id,
            layer=layer,
            signal_type="auto_action",
            severity=severity,
            title=title,
            description=f"Autonomous optimization executed: {title}",
            source_data=context,
            auto_triggered=True,
        )
        self.db.add(signal)
        await self.db.flush()

        return {
            "action": "generate_signal",
            "status": "created",
            "signal_id": str(signal.id),
            "title": title,
        }


class ApprovalQueue:
    """Manage pending approvals for destructive actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_approval_request(
        self,
        workspace_id: UUID,
        rule_id: str,
        rule_name: str,
        actions: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Create an approval request."""
        signal = IntelligenceSignal(
            workspace_id=workspace_id,
            layer="automation",
            signal_type="approval_required",
            severity="warning",
            title=f"Approval Required: {rule_name}",
            description=f"Rule '{rule_name}' triggered and requires approval before executing {len(actions)} actions.",
            source_data={
                "rule_id": rule_id,
                "rule_name": rule_name,
                "actions": actions,
                "context": context,
            },
            recommended_action="Review and approve or reject the pending optimization actions.",
            auto_triggered=False,
        )
        self.db.add(signal)
        await self.db.flush()
        await self.db.refresh(signal)

        return {
            "approval_id": str(signal.id),
            "rule_id": rule_id,
            "rule_name": rule_name,
            "actions_count": len(actions),
            "status": "pending",
        }

    async def approve_action(
        self,
        approval_id: UUID,
    ) -> dict[str, Any]:
        """Approve a pending action."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(IntelligenceSignal).where(IntelligenceSignal.id == approval_id)
        )
        signal = result.scalar_one_or_none()

        if not signal:
            return {"error": "Approval request not found"}

        if signal.acknowledged_at:
            return {"error": "Already processed"}

        signal.acknowledged_at = datetime.utcnow()

        # Execute the actions
        source_data = signal.source_data or {}
        actions = source_data.get("actions", [])
        context = source_data.get("context", {})
        workspace_id = signal.workspace_id

        executor = ActionExecutor(self.db)
        results = await executor.execute_actions(
            actions, workspace_id, signal.brand_id, context
        )

        await self.db.commit()

        return {
            "approval_id": str(approval_id),
            "status": "approved",
            "executed_actions": len(results),
            "results": results,
        }

    async def reject_action(
        self,
        approval_id: UUID,
    ) -> dict[str, Any]:
        """Reject a pending action."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(IntelligenceSignal).where(IntelligenceSignal.id == approval_id)
        )
        signal = result.scalar_one_or_none()

        if not signal:
            return {"error": "Approval request not found"}

        signal.dismissed_at = datetime.utcnow()
        await self.db.commit()

        return {
            "approval_id": str(approval_id),
            "status": "rejected",
        }

    async def list_pending_approvals(
        self,
        workspace_id: UUID,
    ) -> list[dict[str, Any]]:
        """List pending approval requests."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(IntelligenceSignal)
            .where(
                IntelligenceSignal.workspace_id == workspace_id,
                IntelligenceSignal.signal_type == "approval_required",
                IntelligenceSignal.acknowledged_at.is_(None),
                IntelligenceSignal.dismissed_at.is_(None),
            )
            .order_by(IntelligenceSignal.created_at.desc())
        )
        signals = result.scalars().all()

        return [
            {
                "id": str(s.id),
                "rule_name": (s.source_data or {}).get("rule_name", "Unknown"),
                "title": s.title,
                "description": s.description,
                "actions_count": len((s.source_data or {}).get("actions", [])),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ]
