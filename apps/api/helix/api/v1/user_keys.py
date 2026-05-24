"""BYOK — Bring Your Own Key API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.services import user_api_keys as byok_service

router = APIRouter(prefix="/user-keys", tags=["user-keys"])


class UserKeyCreate(BaseModel):
    provider: str
    raw_key: str


class UserKeyRead(BaseModel):
    provider: str
    key_prefix: str
    created_at: str | None = None


class UserKeyList(BaseModel):
    keys: list[UserKeyRead]


@router.get("", response_model=UserKeyList)
async def list_user_keys(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> UserKeyList:
    keys = await byok_service.list_keys(db, user.id)
    return UserKeyList(
        keys=[
            UserKeyRead(
                provider=k.provider,
                key_prefix=k.key_prefix,
                created_at=str(k.created_at) if k.created_at else None,
            )
            for k in keys
        ]
    )


@router.post("", response_model=UserKeyRead, status_code=status.HTTP_201_CREATED)
async def store_user_key(
    payload: UserKeyCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> UserKeyRead:
    valid_providers = {  # noqa: N806
        "openai", "anthropic", "gemini", "openrouter",
        "deepseek", "groq", "mistral", "dashscope",
    }
    if payload.provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported provider. Valid: {', '.join(sorted(valid_providers))}",
        )
    entry = await byok_service.store_key(db, user.id, payload.provider, payload.raw_key)
    return UserKeyRead(
        provider=entry.provider,
        key_prefix=entry.key_prefix,
        created_at=str(entry.created_at) if entry.created_at else None,
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_key(
    provider: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await byok_service.delete_key(db, user.id, provider)
    if not deleted:
        raise HTTPException(status_code=404, detail="No key found for this provider")
