"""Organization endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.schemas.organization import OrganizationRead
from helix.services import organization as org_service

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("/me", response_model=OrganizationRead)
async def get_my_organization(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    """Get the organization for the currently authenticated user."""
    org = await org_service.get_organization(db, user.organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organization not found")
    return OrganizationRead.model_validate(org)

@router.get("/{org_id}", response_model=OrganizationRead)
async def get_organization(
    org_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    """Get a specific organization. Users can only access their own organization."""
    if org_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="access denied")
    
    org = await org_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organization not found")
    return OrganizationRead.model_validate(org)
