"""API key management service."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.enterprise import ApiKey
from helix.models.organization import User
from helix.schemas.enterprise import ApiKeyCreate


def _generate_key() -> tuple[str, str, str]:
    """Generate a helix_ prefixed API key. Returns (raw_key, prefix, hash)."""
    raw = f"helix_{secrets.token_hex(32)}"
    prefix = raw[:16]
    h = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, h


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def create_api_key(
    db: AsyncSession,
    payload: ApiKeyCreate,
    *,
    user: User,
) -> tuple[ApiKey, str]:
    """Create a new API key, returning (model, raw_key)."""
    raw_key, prefix, key_hash = _generate_key()

    key = ApiKey(
        organization_id=user.organization_id,
        user_id=user.id,
        name=payload.name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=payload.scopes,
    )
    db.add(key)
    await db.flush()
    await db.refresh(key)
    return key, raw_key


async def get_api_key(db: AsyncSession, key_id: uuid.UUID) -> ApiKey | None:
    return await db.get(ApiKey, key_id)


async def list_api_keys(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> list[ApiKey]:
    q = select(ApiKey).where(ApiKey.organization_id == organization_id)
    if user_id:
        q = q.where(ApiKey.user_id == user_id)
    q = q.order_by(ApiKey.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_api_key_last_used(db: AsyncSession, key: ApiKey) -> None:
    from datetime import datetime
    key.last_used_at = datetime.now(UTC)
    await db.flush()


async def delete_api_key(db: AsyncSession, key: ApiKey) -> None:
    await db.delete(key)
    await db.flush()


async def resolve_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    """Resolve a raw API key string to an enabled ApiKey row."""
    key_hash = _hash_key(raw_key)
    q = select(ApiKey).where(
        ApiKey.key_hash == key_hash,
        ApiKey.enabled is True,
    )
    result = await db.execute(q)
    return result.scalar_one_or_none()
