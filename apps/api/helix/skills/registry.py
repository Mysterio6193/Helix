"""In-memory registry of parsed manifests + handlers."""
from __future__ import annotations

from helix.skills.base import SkillHandler, SkillManifest

_MANIFESTS: dict[str, SkillManifest] = {}
_HANDLERS: dict[str, SkillHandler] = {}


def upsert_manifest(manifest: SkillManifest) -> None:
    _MANIFESTS[manifest.name] = manifest


def upsert_handler(name: str, handler: SkillHandler) -> None:
    _HANDLERS[name] = handler


def get_manifest(name: str) -> SkillManifest | None:
    return _MANIFESTS.get(name)


def get_handler(name: str) -> SkillHandler | None:
    handler = _HANDLERS.get(name)
    if handler is None:
        manifest = get_manifest(name)
        if manifest and manifest.parent_skill:
            return _HANDLERS.get(manifest.parent_skill)
    return handler


def list_manifests() -> list[SkillManifest]:
    return list(_MANIFESTS.values())


def list_handlers() -> dict[str, SkillHandler]:
    return dict(_HANDLERS)


def clear() -> None:
    _MANIFESTS.clear()
    _HANDLERS.clear()
