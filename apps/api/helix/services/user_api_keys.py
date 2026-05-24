"""BYOK — Bring Your Own Key. Per-user provider API key management.

Keys are encrypted at rest using the server's ENCRYPTION_KEY (Fernet).
The server decrypts them on use to make LLM API calls.
"""
from __future__ import annotations

import uuid

from cryptography.fernet import Fernet
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import get_settings
from helix.models.usage import UserApiKey


def _cipher() -> Fernet:
    key = get_settings().encryption_key
    # Fernet keys must be 32 bytes URL-safe base64 encoded
    if len(key) != 44 or not key.endswith("="):
        # Try padding or use as-is
        pass
    return Fernet(key.encode() if isinstance(key, str) else key)


def _encrypt(plaintext: str) -> str:
    return _cipher().encrypt(plaintext.encode()).decode()


def _decrypt(ciphertext: str) -> str:
    return _cipher().decrypt(ciphertext.encode()).decode()


def _key_prefix(raw: str) -> str:
    return raw[:12] + "..."


async def store_key(
    db: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
    raw_key: str,
) -> UserApiKey:
    """Store an encrypted user API key. Returns the model."""
    existing_q = await db.execute(
        select(UserApiKey).where(
            UserApiKey.user_id == user_id,
            UserApiKey.provider == provider,
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.flush()

    entry = UserApiKey(
        id=uuid.uuid4(),
        user_id=user_id,
        provider=provider,
        key_prefix=_key_prefix(raw_key),
        key_ciphertext=_encrypt(raw_key),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def resolve_plaintext(
    db: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
) -> str | None:
    """Decrypt and return the plaintext key for a user+provider."""
    result = await db.execute(
        select(UserApiKey).where(
            UserApiKey.user_id == user_id,
            UserApiKey.provider == provider,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return None
    return _decrypt(entry.key_ciphertext)


async def list_keys(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[UserApiKey]:
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == user_id)
    )
    return list(result.scalars().all())


async def delete_key(
    db: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
) -> bool:
    result = await db.execute(
        delete(UserApiKey).where(
            UserApiKey.user_id == user_id,
            UserApiKey.provider == provider,
        )
    )
    await db.commit()
    return result.rowcount > 0
