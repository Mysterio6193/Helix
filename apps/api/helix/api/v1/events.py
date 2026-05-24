"""Events API — allows third-party platforms or internal services to publish events."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import assert_workspace_access
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.services.event_bus import publish_event

router = APIRouter(prefix="/events", tags=["events"])


class PublishEventRequest(BaseModel):
    workspace_id: uuid.UUID = Field(..., description="Workspace ID context")
    brand_id: uuid.UUID | None = Field(default=None, description="Optional brand context")
    event_kind: str = Field(
        ...,
        description="Event kind (e.g. roas_dropped, ctr_dropped, campaign_fatigue_detected)",
        min_length=2,
        max_length=128,
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Custom event payload variables"
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def post_event(
    req: PublishEventRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Publish a custom business event to trigger autonomous workflows."""
    await assert_workspace_access(db, user, req.workspace_id)

    count = await publish_event(
        db,
        workspace_id=req.workspace_id,
        brand_id=req.brand_id,
        event_kind=req.event_kind,
        payload=req.payload,
    )

    return {
        "ok": True,
        "event_kind": req.event_kind,
        "triggered_runs_count": count,
    }
