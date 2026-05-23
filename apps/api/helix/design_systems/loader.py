"""Load curated design systems + visual schools from disk into the DB."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import get_settings
from helix.core.db import session_factory
from helix.core.logging import get_logger
from helix.models.design_system import DesignSystem

log = get_logger(__name__)


REQUIRED_FIELDS = ("slug", "name")


def _validate(data: dict[str, Any], path: Path) -> None:
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            raise ValueError(f"{path}: missing required field '{field}'")


def load_design_systems_from_disk(root: Path | None = None) -> list[dict[str, Any]]:
    """Walk YAML files under design-systems/ and return validated dicts."""
    settings = get_settings()
    base = Path(root) if root else Path(settings.design_systems_dir)
    if not base.exists():
        log.warning("design_systems_dir_missing", extra={"path": str(base)})
        return []

    results: list[dict[str, Any]] = []
    for yaml_path in sorted(base.rglob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            _validate(data, yaml_path)
            data["source_path"] = str(yaml_path.relative_to(base))
            # Schools live under schools/ — flag them
            if "schools/" in str(yaml_path.relative_to(base)).replace("\\", "/"):
                data.setdefault("is_school", True)
            results.append(data)
        except Exception as exc:
            log.exception("design_system_parse_failed", extra={"path": str(yaml_path), "error": str(exc)})
    return results


async def sync_design_systems(session: AsyncSession | None = None) -> int:
    """Upsert all on-disk YAML design systems into the database."""
    own_session = session is None

    async def _do(s: AsyncSession) -> int:
        records = load_design_systems_from_disk()
        count = 0
        for rec in records:
            slug = rec["slug"]
            row = await s.scalar(select(DesignSystem).where(DesignSystem.slug == slug))
            payload = {
                "slug": slug,
                "name": rec.get("name", slug),
                "school": rec.get("school"),
                "description": rec.get("description"),
                "palette": rec.get("palette", {}) or {},
                "typography": rec.get("typography", {}) or {},
                "spacing": rec.get("spacing", {}) or {},
                "motion": rec.get("motion", {}) or {},
                "components": rec.get("components", {}) or {},
                "tags": rec.get("tags", []) or [],
                "is_school": bool(rec.get("is_school", False)),
                "enabled": bool(rec.get("enabled", True)),
                "source_path": rec.get("source_path"),
            }
            if row is None:
                s.add(DesignSystem(**payload))
            else:
                for k, v in payload.items():
                    setattr(row, k, v)
            count += 1
        await s.commit()
        log.info("design_systems_synced", extra={"count": count})
        return count

    if own_session:
        async with session_factory() as new_session:
            return await _do(new_session)
    assert session is not None
    return await _do(session)


if __name__ == "__main__":
    asyncio.run(sync_design_systems())
