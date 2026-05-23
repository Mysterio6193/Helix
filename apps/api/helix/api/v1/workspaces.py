"""Workspace CRUD endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import assert_workspace_access
from helix.core.config import get_settings
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.schemas.common import Page
from helix.schemas.organization import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from helix.services import organization as org_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceRead:
    workspace = await org_service.create_workspace(db, user.organization_id, payload)
    await db.commit()
    return WorkspaceRead.model_validate(workspace)

@router.get("", response_model=Page[WorkspaceRead])
async def list_workspaces(
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Page[WorkspaceRead]:
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    items, total = await org_service.list_workspaces_for_user(
        db, user, limit=eff_limit, offset=offset
    )
    return Page[WorkspaceRead](
        items=[WorkspaceRead.model_validate(w) for w in items],
        total=total,
        limit=eff_limit,
        offset=offset,
    )

@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceRead:
    workspace = await assert_workspace_access(db, user, workspace_id)
    return WorkspaceRead.model_validate(workspace)

@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceRead:
    workspace = await assert_workspace_access(db, user, workspace_id)
    workspace = await org_service.update_workspace(db, workspace, payload)
    await db.commit()
    return WorkspaceRead.model_validate(workspace)

@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_workspace(
    workspace_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    workspace = await assert_workspace_access(db, user, workspace_id)
    await org_service.delete_workspace(db, workspace)
    await db.commit()
