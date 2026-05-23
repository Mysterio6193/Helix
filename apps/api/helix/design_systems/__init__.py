"""Design-system library loader (open-design pattern).

Reads YAML files from settings.design_systems_dir and syncs into the
design_systems table. Schools live under schools/ (5 locked visual schools);
brand-name presets under library/ (curated open-design library).
"""
from __future__ import annotations

from .loader import load_design_systems_from_disk, sync_design_systems

__all__ = ["load_design_systems_from_disk", "sync_design_systems"]
