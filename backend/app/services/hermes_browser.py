import asyncio
import base64
import json
import os
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


@dataclass
class BrowserSession:
    session_id: str
    context: BrowserContext
    page: Page
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    viewport_width: int = 1280
    viewport_height: int = 720
    cookies_file: Optional[str] = None

    def update_active(self):
        self.last_active = time.time()


class HermesBrowserService:
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._sessions: dict[str, BrowserSession] = {}
        self._data_dir = Path(__file__).parent.parent.parent / "data" / "browser"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        print("Hermes Browser Service initialized")

    async def shutdown(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
        for session_id in list(self._sessions.keys()):
            await self.destroy_session(session_id)
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        print("Hermes Browser Service shutdown")

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            now = time.time()
            expired = [
                sid for sid, s in self._sessions.items()
                if now - s.last_active > 1800
            ]
            for sid in expired:
                await self.destroy_session(sid)

    async def create_session(
        self,
        session_id: str,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        persist_cookies: bool = True
    ) -> BrowserSession:
        if session_id in self._sessions:
            await self.destroy_session(session_id)

        context = await self._browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Manila",
        )

        cookies_file = None
        if persist_cookies:
            cookies_file = str(self._data_dir / f"{session_id}_cookies.json")
            if os.path.exists(cookies_file):
                try:
                    with open(cookies_file, "r") as f:
                        cookies = json.load(f)
                    await context.add_cookies(cookies)
                except Exception:
                    pass

        page = await context.new_page()

        session = BrowserSession(
            session_id=session_id,
            context=context,
            page=page,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            cookies_file=cookies_file,
        )
        self._sessions[session_id] = session
        return session

    async def destroy_session(self, session_id: str):
        session = self._sessions.pop(session_id, None)
        if not session:
            return
        if session.cookies_file:
            try:
                cookies = await session.context.cookies()
                with open(session.cookies_file, "w") as f:
                    json.dump(cookies, f)
            except Exception:
                pass
        try:
            await session.context.close()
        except Exception:
            pass

    def get_session(self, session_id: str) -> Optional[BrowserSession]:
        session = self._sessions.get(session_id)
        if session:
            session.update_active()
        return session

    async def navigate(self, session_id: str, url: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            response = await session.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )
            session.update_active()

            return {
                "status": "success",
                "url": session.page.url,
                "title": await session.page.title(),
                "status_code": response.status if response else None,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def click(self, session_id: str, ref: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            element = session.page.locator(f"[data-ref='{ref}']")
            if await element.count() == 0:
                element = session.page.get_by_test_id(ref)
            if await element.count() == 0:
                element = session.page.locator(ref)

            await element.first.click(timeout=5000)
            await session.page.wait_for_load_state("domcontentloaded", timeout=10000)
            session.update_active()

            return {
                "status": "success",
                "url": session.page.url,
                "title": await session.page.title(),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def type_text(self, session_id: str, ref: str, text: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            element = session.page.locator(f"[data-ref='{ref}']")
            if await element.count() == 0:
                element = session.page.get_by_test_id(ref)
            if await element.count() == 0:
                element = session.page.locator(ref)

            await element.first.click()
            await element.first.fill(text)
            session.update_active()

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def screenshot(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            screenshot_bytes = await session.page.screenshot(
                type="jpeg",
                quality=80,
                full_page=False
            )
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            session.update_active()

            return {
                "status": "success",
                "screenshot": screenshot_b64,
                "url": session.page.url,
                "title": await session.page.title(),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_snapshot(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            snapshot = await session.page.accessibility.snapshot()
            session.update_active()

            return {
                "status": "success",
                "snapshot": snapshot,
                "url": session.page.url,
                "title": await session.page.title(),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def extract_content(self, session_id: str, selector: str = "body") -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            content = await session.page.evaluate(f"""
                () => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;
                    return {{
                        text: el.innerText,
                        html: el.innerHTML,
                        links: Array.from(el.querySelectorAll('a')).map(a => ({{
                            text: a.innerText,
                            href: a.href
                        }})).slice(0, 50),
                    }};
                }}
            """)
            session.update_active()

            return {
                "status": "success",
                "content": content,
                "url": session.page.url,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def scroll(self, session_id: str, direction: str = "down", amount: int = 500) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            delta = amount if direction == "down" else -amount
            await session.page.mouse.wheel(0, delta)
            await asyncio.sleep(0.5)
            session.update_active()

            return {"status": "success", "direction": direction, "amount": amount}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def go_back(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            await session.page.go_back()
            session.update_active()
            return {
                "status": "success",
                "url": session.page.url,
                "title": await session.page.title(),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def go_forward(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            await session.page.go_forward()
            session.update_active()
            return {
                "status": "success",
                "url": session.page.url,
                "title": await session.page.title(),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def execute_javascript(self, session_id: str, script: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            result = await session.page.evaluate(script)
            session.update_active()
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def search_google(self, session_id: str, query: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        try:
            await session.page.goto(
                f"https://www.google.com/search?q={query}",
                wait_until="domcontentloaded",
                timeout=30000
            )
            session.update_active()

            results = await session.page.evaluate("""
                () => {
                    const items = document.querySelectorAll('div.g');
                    return Array.from(items).slice(0, 10).map(item => {
                        const title = item.querySelector('h3')?.innerText || '';
                        const link = item.querySelector('a')?.href || '';
                        const snippet = item.querySelector('.VwiC3b')?.innerText || '';
                        return { title, link, snippet };
                    });
                }
            """)

            return {
                "status": "success",
                "query": query,
                "results": results,
                "url": session.page.url,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_sessions(self) -> list[dict]:
        return [
            {
                "session_id": s.session_id,
                "url": s.page.url if s.page else None,
                "created_at": s.created_at,
                "last_active": s.last_active,
            }
            for s in self._sessions.values()
        ]


hermes_browser = HermesBrowserService()
