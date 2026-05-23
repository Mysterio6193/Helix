"""Brand CRUD endpoints — all routes require auth + workspace ACL."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import (
    assert_brand_access,
    assert_workspace_access,
    get_default_workspace_for_user,
    list_user_workspace_ids,
)
from helix.core.config import get_settings
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.schemas.brand import BrandCreate, BrandRead, BrandUpdate
from helix.schemas.common import Page
from helix.services import brand as brand_service

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> BrandRead:
    # Resolve target workspace: explicit payload wins, else default for caller's org.
    if payload.workspace_id is not None:
        await assert_workspace_access(db, user, payload.workspace_id)
    else:
        ws = await get_default_workspace_for_user(db, user)
        payload = payload.model_copy(update={"workspace_id": ws.id})
    brand = await brand_service.create_brand(db, payload)
    await db.commit()
    return BrandRead.model_validate(brand)


@router.get("", response_model=Page[BrandRead])
async def list_brands(
    workspace_id: UUID | None = None,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Page[BrandRead]:
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    if workspace_id is not None:
        await assert_workspace_access(db, user, workspace_id)
        items, total = await brand_service.list_brands(
            db, workspace_id=workspace_id, limit=eff_limit, offset=offset
        )
    else:
        # Scope to all workspaces the caller's org owns
        ws_ids = await list_user_workspace_ids(db, user)
        items, total = await brand_service.list_brands_in_workspaces(
            db, workspace_ids=ws_ids, limit=eff_limit, offset=offset
        )
    return Page[BrandRead](
        items=[BrandRead.model_validate(b) for b in items],
        total=total,
        limit=eff_limit,
        offset=offset,
    )


@router.get("/{brand_id}", response_model=BrandRead)
async def get_brand(
    brand_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> BrandRead:
    brand = await assert_brand_access(db, user, brand_id)
    return BrandRead.model_validate(brand)


@router.patch("/{brand_id}", response_model=BrandRead)
async def update_brand(
    brand_id: UUID,
    payload: BrandUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> BrandRead:
    brand = await assert_brand_access(db, user, brand_id)
    brand = await brand_service.update_brand(db, brand, payload)
    await db.commit()
    return BrandRead.model_validate(brand)


@router.delete(
    "/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_brand(
    brand_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    brand = await assert_brand_access(db, user, brand_id)
    await brand_service.delete_brand(db, brand)
    await db.commit()
