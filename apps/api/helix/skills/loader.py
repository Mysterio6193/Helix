"""Skill loader: walks `skills/` for SKILL.md files, syncs to DB + registry.

Loads python_frontmatter + YAML metadata, validates trigger phrases (marketingskills
contract), then upserts both the in-memory registry and `skills_registry` table.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
import uuid
from collections.abc import Iterable
from pathlib import Path

import frontmatter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.models.skill import SkillRegistry
from helix.skills import handlers as handlers_package
from helix.skills.base import SkillManifest, drain_pending_handlers
from helix.skills.registry import upsert_handler, upsert_manifest

log = get_logger("helix.skills.loader")

REQUIRED_FIELDS = {"name", "description"}


def _validate(meta: dict, path: Path) -> None:
    missing = REQUIRED_FIELDS - set(meta.keys())
    if missing:
        raise ValueError(f"SKILL.md at {path} missing fields: {missing}")
    if "Trigger phrases:" not in meta.get("description", "") and "trigger phrases" not in (
        " ".join(meta.get("tags", [])).lower()
    ):
        # Soft warning: marketingskills convention is to embed trigger phrases in description.
        log.warning("skill.missing_trigger_phrases", path=str(path), name=meta.get("name"))


def parse_skill_md(path: Path) -> SkillManifest:
    fm = frontmatter.load(path)
    meta = fm.metadata or {}
    _validate(meta, path)
    return SkillManifest(
        name=str(meta["name"]),
        description=str(meta.get("description", "")),
        version=str(meta.get("version", "1.0.0")),
        inputs=meta.get("inputs", {}) or {},
        outputs=meta.get("outputs", {}) or {},
        required_tools=list(meta.get("required_tools", []) or []),
        dependencies=list(meta.get("dependencies", []) or []),
        tags=list(meta.get("tags", []) or []),
        trigger_phrases=list(meta.get("trigger_phrases", []) or []),
        manifest_path=str(path),
        is_stub="_stubs" in path.parts or bool(meta.get("stub")),
        is_specialization=bool(meta.get("is_specialization", False)),
        parent_skill=meta.get("parent_skill"),
        brand_id=str(meta["brand_id"]) if meta.get("brand_id") else None,
    )


def discover_manifests(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("SKILL.md"))


def _import_all_handlers(reload: bool = False) -> None:
    """Eagerly import every submodule of helix.skills.handlers so decorators register."""
    pkg = handlers_package
    for module_info in pkgutil.walk_packages(pkg.__path__, prefix=f"{pkg.__name__}."):
        try:
            if reload and module_info.name in sys.modules:
                importlib.reload(sys.modules[module_info.name])
            else:
                importlib.import_module(module_info.name)
        except Exception as exc:  # noqa: BLE001
            log.exception("skills.handler_import_failed", module=module_info.name, error=str(exc), reload=reload)


async def sync_registry(db: AsyncSession | None = None, reload_handlers: bool = False) -> dict[str, int]:
    """Walk skills dir, register manifests in memory + DB, bind handlers by name."""
    if db is None:
        from helix.core.db import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            try:
                res = await sync_registry(session, reload_handlers=reload_handlers)
                await session.commit()
                return res
            except Exception:
                await session.rollback()
                raise

    settings = get_settings()
    root = settings.skills_dir
    paths = list(discover_manifests(root))

    # Also discover marketing skills from packages/vendor/marketingskills/skills
    marketing_skills_dir = Path(__file__).resolve().parents[4] / "packages/vendor/marketingskills/skills"
    if marketing_skills_dir.exists():
        paths.extend(discover_manifests(marketing_skills_dir))

    counts = {"manifests": 0, "handlers": 0, "stubs": 0}
    _import_all_handlers(reload=reload_handlers)
    pending = drain_pending_handlers()
    for name, handler in pending.items():
        upsert_handler(name, handler)
    counts["handlers"] = len(pending)

    for path in paths:
        try:
            manifest = parse_skill_md(path)
        except Exception as exc:  # noqa: BLE001
            log.exception("skill.parse_failed", path=str(path), error=str(exc))
            continue

        upsert_manifest(manifest)
        counts["manifests"] += 1
        if manifest.is_stub:
            counts["stubs"] += 1

        existing = (
            await db.execute(select(SkillRegistry).where(SkillRegistry.name == manifest.name))
        ).scalar_one_or_none()

        parsed_brand_id = None
        if manifest.brand_id:
            try:
                parsed_brand_id = uuid.UUID(manifest.brand_id)
            except ValueError:
                log.warning("skill.invalid_brand_id", brand_id=manifest.brand_id, skill=manifest.name)

        if existing is None:
            row = SkillRegistry(
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                manifest_path=manifest.manifest_path,
                handler_path=f"helix.skills.handlers:{manifest.name}" if manifest.name in pending else None,
                inputs=manifest.inputs,
                outputs=manifest.outputs,
                required_tools=manifest.required_tools,
                dependencies=manifest.dependencies,
                tags=manifest.tags,
                trigger_phrases=manifest.trigger_phrases,
                is_stub=manifest.is_stub,
                is_specialization=manifest.is_specialization,
                parent_skill=manifest.parent_skill,
                brand_id=parsed_brand_id,
            )
            db.add(row)
        else:
            existing.version = manifest.version
            existing.description = manifest.description
            existing.manifest_path = manifest.manifest_path
            existing.inputs = manifest.inputs
            existing.outputs = manifest.outputs
            existing.required_tools = manifest.required_tools
            existing.dependencies = manifest.dependencies
            existing.tags = manifest.tags
            existing.trigger_phrases = manifest.trigger_phrases
            existing.is_stub = manifest.is_stub
            existing.is_specialization = manifest.is_specialization
            existing.parent_skill = manifest.parent_skill
            existing.brand_id = parsed_brand_id

    await db.flush()
    log.info("skills.synced", **counts, root=str(root))
    return counts


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    from helix.core.db import AsyncSessionLocal

    async def _main() -> None:
        async with AsyncSessionLocal() as db:
            await sync_registry(db)
            await db.commit()

    asyncio.run(_main())
