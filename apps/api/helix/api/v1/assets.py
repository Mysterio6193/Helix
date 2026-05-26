"""Assets API: list / detail / signed URL — all auth-gated and ACL-checked."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import (
    assert_brand_access,
    list_user_workspace_ids,
)
from helix.core.config import get_settings
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.organization import User, Workspace
from helix.models.workflow import Asset

router = APIRouter(prefix="/assets", tags=["assets"])


def _asset_to_public(a: Asset) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "brand_id": str(a.brand_id) if a.brand_id else None,
        "workflow_run_id": str(a.workflow_run_id) if a.workflow_run_id else None,
        "kind": a.kind,
        "purpose": a.purpose,
        "mime_type": a.mime_type,
        "s3_key": a.s3_key,
        "storage_url": a.storage_url,
        "text_content": a.text_content,
        "width": a.width,
        "height": a.height,
        "metadata": a.metadata_ or {},
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


async def _assert_asset_access(db: AsyncSession, user: User, asset: Asset) -> None:
    """Asset access requires the caller to own the brand OR (when brand_id is null)
    the asset's workspace."""
    if asset.brand_id is not None:
        await assert_brand_access(db, user, asset.brand_id)
        return
    if asset.workspace_id is not None:
        ws = await db.get(Workspace, asset.workspace_id)
        if ws is None or ws.organization_id != user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="asset access denied")
        return
    # Orphan assets (no brand, no workspace) are admin-only — deny by default.
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="asset access denied")


@router.get("")
async def list_assets(
    brand_id: uuid.UUID | None = Query(default=None),
    workflow_run_id: uuid.UUID | None = Query(default=None),
    kind: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    ws_ids = await list_user_workspace_ids(db, user)
    stmt = select(Asset).order_by(desc(Asset.created_at))
    # Default scope: assets in caller-owned workspaces.
    stmt = stmt.where(Asset.workspace_id.in_(ws_ids))

    if brand_id is not None:
        await assert_brand_access(db, user, brand_id)
        stmt = stmt.where(Asset.brand_id == brand_id)
    if workflow_run_id is not None:
        stmt = stmt.where(Asset.workflow_run_id == workflow_run_id)
    if kind:
        stmt = stmt.where(Asset.kind == kind)
    stmt = stmt.offset(offset).limit(eff_limit)
    rows = list((await db.execute(stmt)).scalars().all())
    return [_asset_to_public(a) for a in rows]


@router.get("/{asset_id}")
async def get_asset(
    asset_id: uuid.UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    row = (
        await db.execute(select(Asset).where(Asset.id == asset_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="asset not found")
    await _assert_asset_access(db, user, row)
    return _asset_to_public(row)


@router.get("/{asset_id}/url")
async def get_asset_url(
    asset_id: uuid.UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Return presigned S3 URL for asset download/display.

    Returns 503 if the storage backend cannot presign — never falls back to a
    placeholder image, which would silently misrepresent the asset.
    """
    settings = get_settings()
    row = (
        await db.execute(select(Asset).where(Asset.id == asset_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="asset not found")
    await _assert_asset_access(db, user, row)

    from helix.core.storage import get_storage

    if not row.s3_key:
        raise HTTPException(status_code=404, detail="asset has no storage key")
    try:
        url = get_storage().presign_get(row.s3_key, ttl_seconds=settings.asset_presign_ttl_seconds)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"asset storage unavailable: {exc}",
        ) from exc
    return {"url": url}


@router.get("/{asset_id}/thumbnail")
async def get_asset_thumbnail(
    asset_id: uuid.UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Return presigned URL for webp thumbnail variant.

    Returns 503 on storage failure rather than a placeholder image.
    """
    settings = get_settings()
    row = (
        await db.execute(select(Asset).where(Asset.id == asset_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="asset not found")
    await _assert_asset_access(db, user, row)

    from helix.core.storage import get_storage

    if not row.s3_key:
        raise HTTPException(status_code=404, detail="asset has no storage key")
    try:
        thumb_key = row.s3_key.rsplit(".", 1)[0] + settings.asset_thumbnail_suffix
        url = get_storage().presign_get(thumb_key, ttl_seconds=settings.asset_presign_ttl_seconds)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"asset thumbnail unavailable: {exc}",
        ) from exc
    return {"url": url}
