"""All workflow slices auto-register on import.

Importing this package wires every slice into the `_WORKFLOWS` registry
so the worker (and the API) can look them up by name.
"""
from __future__ import annotations

# Each slice module calls `register_workflow(...)` at import time.
# Lazy guard so missing slice modules don't crash bootstrap.
import importlib

for _mod in (
    "helix.workflows.slices.brand_identity_foundation",
    "helix.workflows.slices.packaging_suite",
    "helix.workflows.slices.website_suite",
    "helix.workflows.slices.social_pack",
    "helix.workflows.slices.menu_design",
    "helix.workflows.slices.launch_campaign",
    "helix.workflows.slices.boardroom_suite",
):
    try:
        importlib.import_module(_mod)
    except ImportError:
        # Slice not yet implemented — that's fine, will be added in later phases.
        pass
