"""Background file watcher for hot-reloading skills and design systems."""
from __future__ import annotations

import asyncio
from pathlib import Path

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.skills.loader import sync_registry
from helix.design_systems.loader import sync_design_systems

log = get_logger("helix.core.watcher")

# Active watch task
_watcher_task: asyncio.Task | None = None

async def _trigger_sync() -> None:
    """Debounced execution of skill and design system synchronization."""
    try:
        log.info("watcher.sync_triggered")
        # Sync skills with reload_handlers=True to import/reload dynamic modules
        skills_counts = await sync_registry(reload_handlers=True)
        log.info("watcher.skills_synced", **skills_counts)

        # Sync design systems
        ds_count = await sync_design_systems()
        log.info("watcher.design_systems_synced", count=ds_count)
    except Exception as exc:
        log.exception("watcher.sync_failed", error=str(exc))

async def _watch_with_watchfiles(paths: list[Path]) -> None:
    """Watch files using the watchfiles library."""
    from watchfiles import awatch

    log.info("watcher.watchfiles_started", paths=[str(p) for p in paths])
    async for changes in awatch(*paths):
        # changes is a set of (Change, filepath)
        valid_changes = []
        for _, filepath in changes:
            p = Path(filepath)
            # Skip temp or system files if any
            if p.name.startswith(".") or p.name.endswith("~"):
                continue
            valid_changes.append(filepath)

        if valid_changes:
            log.info("watcher.file_changes_detected", count=len(valid_changes))
            await _trigger_sync()

async def _watch_with_polling(paths: list[Path], interval_seconds: float = 1.0) -> None:
    """Fallback file watcher using polling for file modification times."""
    log.info("watcher.polling_fallback_started", paths=[str(p) for p in paths])

    def get_file_mtimes() -> dict[Path, float]:
        mtimes = {}
        for root_path in paths:
            if not root_path.exists():
                continue
            if root_path.is_file():
                mtimes[root_path] = root_path.stat().st_mtime
            else:
                for file_path in root_path.rglob("*"):
                    if file_path.is_file() and not file_path.name.startswith(".") and not file_path.name.endswith("~"):
                        try:
                            mtimes[file_path] = file_path.stat().st_mtime
                        except FileNotFoundError:
                            pass
        return mtimes

    # Initial state
    last_mtimes = get_file_mtimes()

    while True:
        await asyncio.sleep(interval_seconds)
        current_mtimes = get_file_mtimes()

        # Check if anything changed
        changed = False
        if current_mtimes.keys() != last_mtimes.keys():
            changed = True
            added = current_mtimes.keys() - last_mtimes.keys()
            removed = last_mtimes.keys() - current_mtimes.keys()
            log.info("watcher.polling.structure_changed", added=len(added), removed=len(removed))
        else:
            for path, current_mtime in current_mtimes.items():
                if last_mtimes.get(path) != current_mtime:
                    changed = True
                    log.info("watcher.polling.file_modified", file=str(path))
                    break

        if changed:
            last_mtimes = current_mtimes
            await _trigger_sync()

async def start_watcher() -> None:
    """Start the background file watcher task."""
    global _watcher_task
    if _watcher_task is not None:
        log.warning("watcher.already_running")
        return

    settings = get_settings()
    skills_path = Path(settings.skills_dir).resolve()
    ds_path = Path(settings.design_systems_dir / "library").resolve()

    # Ensure paths exist
    skills_path.mkdir(parents=True, exist_ok=True)
    ds_path.mkdir(parents=True, exist_ok=True)

    paths_to_watch = [skills_path, ds_path]

    try:
        import watchfiles  # noqa: F401
        # Run using watchfiles library
        _watcher_task = asyncio.create_task(_watch_with_watchfiles(paths_to_watch))
    except ImportError:
        log.warning("watcher.watchfiles_missing_using_polling_fallback")
        # Run using polling fallback
        _watcher_task = asyncio.create_task(_watch_with_polling(paths_to_watch))

async def stop_watcher() -> None:
    """Stop the background file watcher task."""
    global _watcher_task
    if _watcher_task is None:
        return

    log.info("watcher.stopping")
    _watcher_task.cancel()
    try:
        await _watcher_task
    except asyncio.CancelledError:
        pass
    _watcher_task = None
    log.info("watcher.stopped")
