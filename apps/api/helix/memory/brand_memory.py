"""Foundation context every skill reads first (marketingskills `product-marketing-context`)."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.brand import Brand, BrandAsset
from helix.models.workflow import Asset


async def load_brand_context(
    db: AsyncSession, brand_id: uuid.UUID, *, recent_assets: int = 10
) -> dict[str, Any]:
    """Return the canonical brand context dictionary consumed by every skill."""
    brand_q = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_q.scalar_one_or_none()
    if brand is None:
        return {}

    brand_assets_q = await db.execute(
        select(BrandAsset).where(BrandAsset.brand_id == brand_id).order_by(BrandAsset.version.desc())
    )
    brand_assets = list(brand_assets_q.scalars().all())

    recent_q = await db.execute(
        select(Asset)
        .where(Asset.brand_id == brand_id)
        .order_by(desc(Asset.created_at))
        .limit(recent_assets)
    )
    recent = list(recent_q.scalars().all())

    palette = next((a.payload for a in brand_assets if a.kind == "palette"), {})
    typography = next((a.payload for a in brand_assets if a.kind == "typography"), {})
    logos = [a for a in brand_assets if a.kind == "logo"]

    return {
        "brand_id": str(brand.id),
        "name": brand.name,
        "slug": brand.slug,
        "category": brand.category,
        "tagline": brand.tagline,
        "mission": brand.mission,
        "story": brand.story,
        "positioning": brand.positioning,
        "archetype": brand.archetype,
        "design_school": brand.design_school,
        "target_audience": brand.target_audience,
        "voice_attributes": brand.voice_attributes,
        "status": brand.status,
        "palette": palette,
        "typography": typography,
        "logos": [
            {"id": str(a.id), "s3_key": a.s3_key, "version": a.version, "is_primary": a.is_primary}
            for a in logos
        ],
        "recent_assets": [
            {
                "id": str(a.id),
                "kind": a.kind,
                "s3_key": a.s3_key,
                "mime_type": a.mime_type,
                "metadata": a.metadata_,
            }
            for a in recent
        ],
    }
