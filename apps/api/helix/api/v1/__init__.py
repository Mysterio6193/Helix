"""v1 API surface."""
from __future__ import annotations

from fastapi import APIRouter

from helix.api.v1 import (
    assets,
    auth,
    billing,
    brands,
    browser,
    enterprise,
    events,
    integrations,
    intelligence,
    llm,
    mcp,
    media,
    memory,
    operating_system,
    organizations,
    power,
    public,
    runs,
    sessions,
    skills,
    telegram,
    user_keys,
    websocket,
    workflows,
    workspaces,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(billing.router)
api_router.include_router(organizations.router)
api_router.include_router(workspaces.router)
api_router.include_router(brands.router)
api_router.include_router(runs.router)
api_router.include_router(integrations.router)
api_router.include_router(skills.router)
api_router.include_router(memory.router)
api_router.include_router(operating_system.router)
api_router.include_router(intelligence.router)
api_router.include_router(assets.router)
api_router.include_router(workflows.router)
api_router.include_router(llm.router)
api_router.include_router(mcp.router)
api_router.include_router(telegram.router)
api_router.include_router(sessions.router)
api_router.include_router(enterprise.router)
api_router.include_router(events.router)
api_router.include_router(user_keys.router)
api_router.include_router(websocket.router)
api_router.include_router(browser.router)
api_router.include_router(media.router)
api_router.include_router(public.router)
api_router.include_router(power.router)
