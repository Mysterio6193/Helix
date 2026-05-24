"""Real Playwright-based browser execution service.

Replaces mock browser automation with headless Chromium.
Manages per-session browser contexts with proper lifecycle.
"""
from __future__ import annotations

import asyncio
import base64
import time
import uuid
from typing import Any

from helix.core.config import settings
from helix.core.logging import get_logger

log = get_logger("helix.browser_executor")

try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright

    _pw_available = True
except ImportError:
    _pw_available = False
    Browser = None
    BrowserContext = None
    Page = None


class BrowserNotAvailable(RuntimeError):
    """Playwright or Chromium not installed."""


class BrowserSession:
    """A single browser session with its own context."""

    def __init__(self, context: BrowserContext, session_id: str):
        self.context = context
        self.session_id = session_id
        self.pages: list[Page] = []
        self.created_at = time.time()

    @property
    def current_url(self) -> str:
        if not self.pages:
            return ""
        try:
            return self.pages[-1].url
        except Exception:
            return ""

    @property
    def page_title(self) -> str:
        if not self.pages:
            return ""
        try:
            return self.pages[-1].title
        except Exception:
            return ""


class BrowserExecutor:
    """Manages a persistent Playwright browser with isolated contexts per session."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._browser: Browser | None = None
        self._playwright = None
        self._sessions: dict[str, BrowserSession] = {}

    async def ensure_browser(self) -> Browser:
        if self._browser and self._browser.is_connected():
            return self._browser
        if not _pw_available:
            raise BrowserNotAvailable("playwright not installed")
        p = await async_playwright().start()
        self._playwright = p
        self._browser = await p.chromium.launch(
            headless=settings.browser_headless,
            executable_path=settings.browser_executable_path or None,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        log.info("browser.launched")
        return self._browser

    async def create_session(self, session_id: str | None = None) -> BrowserSession:
        sid = session_id or str(uuid.uuid4())
        browser = await self.ensure_browser()
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        session = BrowserSession(context, sid)
        self._sessions[sid] = session
        log.info("browser.session_created", session_id=sid)
        return session

    async def get_or_create_session(self, session_id: str) -> BrowserSession:
        if session_id in self._sessions:
            return self._sessions[session_id]
        return await self.create_session(session_id)

    async def close_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session:
            try:
                await session.context.close()
            except Exception:
                pass
            log.info("browser.session_closed", session_id=session_id)

    async def navigate(
        self, session_id: str, url: str, timeout: int = 30000
    ) -> dict[str, Any]:
        session = await self.get_or_create_session(session_id)
        page = await session.context.new_page()
        session.pages.append(page)
        start = time.monotonic()
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            elapsed = (time.monotonic() - start) * 1000
            return {
                "ok": True,
                "url": page.url,
                "title": await page.title(),
                "status_code": resp.status if resp else None,
                "latency_ms": round(elapsed, 1),
            }
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "error": str(exc), "latency_ms": round(elapsed, 1)}

    async def click(
        self, session_id: str, selector: str, timeout: int = 5000
    ) -> dict[str, Any]:
        session = await self.get_or_create_session(session_id)
        page = session.pages[-1] if session.pages else await session.context.new_page()
        if not session.pages:
            session.pages.append(page)
        start = time.monotonic()
        try:
            await page.click(selector, timeout=timeout)
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": True, "url": page.url, "latency_ms": round(elapsed, 1)}
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "error": str(exc), "latency_ms": round(elapsed, 1)}

    async def type_text(
        self, session_id: str, selector: str, text: str, timeout: int = 5000
    ) -> dict[str, Any]:
        session = await self.get_or_create_session(session_id)
        page = session.pages[-1] if session.pages else await session.context.new_page()
        if not session.pages:
            session.pages.append(page)
        start = time.monotonic()
        try:
            await page.fill(selector, text, timeout=timeout)
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": True, "url": page.url, "latency_ms": round(elapsed, 1)}
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "error": str(exc), "latency_ms": round(elapsed, 1)}

    async def screenshot(
        self, session_id: str, full_page: bool = True
    ) -> dict[str, Any]:
        session = await self.get_or_create_session(session_id)
        if not session.pages:
            return {"ok": False, "error": "no pages in session"}
        page = session.pages[-1]
        start = time.monotonic()
        try:
            png_bytes = await page.screenshot(full_page=full_page)
            b64 = base64.b64encode(png_bytes).decode()
            elapsed = (time.monotonic() - start) * 1000
            return {
                "ok": True,
                "screenshot_base64": b64,
                "latency_ms": round(elapsed, 1),
            }
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "error": str(exc), "latency_ms": round(elapsed, 1)}

    async def scroll(
        self, session_id: str, delta_x: int = 0, delta_y: int = 300
    ) -> dict[str, Any]:
        session = await self.get_or_create_session(session_id)
        if not session.pages:
            return {"ok": False, "error": "no pages in session"}
        page = session.pages[-1]
        start = time.monotonic()
        try:
            await page.evaluate(f"window.scrollBy({delta_x}, {delta_y})")
            await asyncio.sleep(0.3)
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": True, "latency_ms": round(elapsed, 1)}
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "error": str(exc), "latency_ms": round(elapsed, 1)}

    async def execute_js(
        self, session_id: str, script: str
    ) -> dict[str, Any]:
        session = await self.get_or_create_session(session_id)
        if not session.pages:
            return {"ok": False, "error": "no pages in session"}
        page = session.pages[-1]
        start = time.monotonic()
        try:
            result = await page.evaluate(script)
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": True, "result": result, "latency_ms": round(elapsed, 1)}
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "error": str(exc), "latency_ms": round(elapsed, 1)}

    async def extract_text(
        self, session_id: str, selector: str | None = None
    ) -> dict[str, Any]:
        session = await self.get_or_create_session(session_id)
        if not session.pages:
            return {"ok": False, "error": "no pages in session"}
        page = session.pages[-1]
        start = time.monotonic()
        try:
            if selector:
                elements = await page.query_selector_all(selector)
                texts = [await el.inner_text() for el in elements]
            else:
                texts = [await page.inner_text("body")]
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": True, "texts": texts, "latency_ms": round(elapsed, 1)}
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "error": str(exc), "latency_ms": round(elapsed, 1)}

    async def cleanup(self) -> None:
        for sid in list(self._sessions.keys()):
            await self.close_session(sid)
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        log.info("browser.cleanup")


# Singleton
_executor: BrowserExecutor | None = None


async def get_executor() -> BrowserExecutor:
    global _executor
    if _executor is None:
        _executor = BrowserExecutor()
    await _executor.ensure_browser()
    return _executor
