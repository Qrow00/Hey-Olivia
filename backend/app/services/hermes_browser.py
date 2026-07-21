import asyncio
import base64
import json
import os
import time
import queue
import threading
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class BrowserSession:
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    viewport_width: int = 1280
    viewport_height: int = 720

    def update_active(self):
        self.last_active = time.time()


class _BrowserWorker:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._queue: queue.Queue = queue.Queue()
        self._results: dict[str, queue.Queue] = {}
        self._playwright = None
        self._browser = None
        self._contexts: dict[str, Any] = {}
        self._pages: dict[str, Any] = {}
        self._ready = threading.Event()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=15)

    def _run(self):
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            try:
                self._browser = self._playwright.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                print("Hermes Browser initialized (headless=False)")
            except Exception:
                self._browser = self._playwright.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                print("Hermes Browser initialized (headless=True)")
            self._ready.set()
        except Exception as e:
            print(f"[HERMES BROWSER] Init failed: {e}")
            self._ready.set()
            return

        while True:
            try:
                task_id, func, args, kwargs = self._queue.get(timeout=1)
                if task_id is None:
                    break
                try:
                    result = func(*args, **kwargs)
                    self._results[task_id].put(("ok", result))
                except Exception as e:
                    self._results[task_id].put(("error", str(e)))
            except queue.Empty:
                continue
            except Exception:
                break

    def call_sync(self, func, *args, **kwargs) -> tuple[str, Any]:
        task_id = f"{time.time()}_{id(func)}_{threading.current_thread().ident}"
        result_queue = queue.Queue()
        self._results[task_id] = result_queue
        self._queue.put((task_id, func, args, kwargs))
        try:
            status, result = result_queue.get(timeout=60)
            return status, result
        except queue.Empty:
            return "error", "Timeout"
        finally:
            self._results.pop(task_id, None)

    def is_ready(self) -> bool:
        return self._browser is not None

    def stop(self):
        self._queue.put((None, None, None, None))


_worker = _BrowserWorker()


class HermesBrowserService:
    def __init__(self):
        self._sessions: dict[str, BrowserSession] = {}
        self._data_dir = Path(__file__).parent.parent.parent / "data" / "browser"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        await asyncio.to_thread(_worker.start)
        self._initialized = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        print("Hermes Browser Service ready")

    async def shutdown(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
        for session_id in list(self._sessions.keys()):
            await self.destroy_session(session_id)
        _worker.stop()
        print("Hermes Browser Service shutdown")

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            now = time.time()
            expired = [sid for sid, s in self._sessions.items() if now - s.last_active > 1800]
            for sid in expired:
                await self.destroy_session(sid)

    async def _call(self, func, *args, **kwargs):
        return await asyncio.to_thread(_worker.call_sync, func, *args, **kwargs)

    async def create_session(self, session_id: str, viewport_width: int = 1280, viewport_height: int = 720, persist_cookies: bool = True) -> BrowserSession:
        if not _worker.is_ready():
            raise Exception("Browser not initialized")

        if session_id in self._sessions:
            await self.destroy_session(session_id)

        def _create():
            context = _worker._browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="Asia/Manila",
            )
            if persist_cookies:
                cookies_file = str(self._data_dir / f"{session_id}_cookies.json")
                if os.path.exists(cookies_file):
                    try:
                        with open(cookies_file, "r") as f:
                            cookies = json.load(f)
                        context.add_cookies(cookies)
                    except Exception:
                        pass
            page = context.new_page()
            _worker._contexts[session_id] = context
            _worker._pages[session_id] = page
            return session_id

        status, result = await self._call(_create)
        if status == "error":
            raise Exception(result)

        session = BrowserSession(session_id=session_id, viewport_width=viewport_width, viewport_height=viewport_height)
        self._sessions[session_id] = session
        return session

    async def destroy_session(self, session_id: str):
        self._sessions.pop(session_id, None)
        _worker._pages.pop(session_id, None)
        context = _worker._contexts.pop(session_id, None)

        if context:
            def _destroy():
                try:
                    context.close()
                except Exception:
                    pass
            await self._call(_destroy)

    def get_session(self, session_id: str) -> Optional[BrowserSession]:
        session = self._sessions.get(session_id)
        if session:
            session.update_active()
        return session

    def _get_page(self, session_id: str):
        return _worker._pages.get(session_id)

    async def navigate(self, session_id: str, url: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        is_youtube = "youtube.com" in url or "youtu.be" in url

        def _nav():
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if is_youtube:
                try:
                    page.wait_for_selector("ytd-search, ytd-video-renderer, ytd-rich-grid-renderer", timeout=8000)
                except Exception:
                    pass
                try:
                    consent = page.locator("button:has-text('Accept all'), button:has-text('I agree'), button:has-text('Reject all')")
                    if consent.count() > 0:
                        consent.first.click(timeout=3000)
                        page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass
            title = page.title()
            return {"status": "success", "url": page.url, "title": title, "status_code": response.status if response else None}

        status, result = await self._call(_nav)
        return result if status == "ok" else {"status": "error", "message": result}

    async def click(self, session_id: str, ref: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _click():
            element = page.locator(f"[data-ref='{ref}']")
            if element.count() == 0:
                element = page.get_by_test_id(ref)
            if element.count() == 0:
                element = page.locator(ref)
            element.first.click(timeout=5000)
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            return {"status": "success", "url": page.url, "title": page.title()}

        status, result = await self._call(_click)
        return result if status == "ok" else {"status": "error", "message": result}

    async def type_text(self, session_id: str, ref: str, text: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _type():
            element = page.locator(f"[data-ref='{ref}']")
            if element.count() == 0:
                element = page.get_by_test_id(ref)
            if element.count() == 0:
                element = page.locator(ref)
            element.first.click()
            element.first.fill(text)
            return {"status": "success"}

        status, result = await self._call(_type)
        return result if status == "ok" else {"status": "error", "message": result}

    async def screenshot(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _shot():
            data = page.screenshot(type="jpeg", quality=80, full_page=False)
            return base64.b64encode(data).decode()

        status, result = await self._call(_shot)
        if status == "ok":
            title = await self._call(page.title)
            return {"status": "success", "screenshot": result, "url": page.url, "title": title[1] if title[0] == "ok" else ""}
        return {"status": "error", "message": result}

    async def get_snapshot(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        status, result = await self._call(page.accessibility.snapshot)
        if status == "ok":
            title = await self._call(page.title)
            return {"status": "success", "snapshot": result, "url": page.url, "title": title[1] if title[0] == "ok" else ""}
        return {"status": "error", "message": result}

    async def scroll(self, session_id: str, direction: str = "down", amount: int = 500) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _scroll():
            delta = amount if direction == "down" else -amount
            page.mouse.wheel(0, delta)
            time.sleep(0.5)
            return {"status": "success", "direction": direction, "amount": amount}

        status, result = await self._call(_scroll)
        return result if status == "ok" else {"status": "error", "message": result}

    async def go_back(self, session_id: str) -> dict:
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _back():
            page.go_back()
            return {"status": "success", "url": page.url, "title": page.title()}

        status, result = await self._call(_back)
        return result if status == "ok" else {"status": "error", "message": result}

    async def go_forward(self, session_id: str) -> dict:
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _fwd():
            page.go_forward()
            return {"status": "success", "url": page.url, "title": page.title()}

        status, result = await self._call(_fwd)
        return result if status == "ok" else {"status": "error", "message": result}

    async def search_google(self, session_id: str, query: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _search():
            page.goto(f"https://www.google.com/search?q={query}", wait_until="domcontentloaded", timeout=30000)
            results = page.evaluate("""
                () => {
                    const items = document.querySelectorAll('div.g');
                    return Array.from(items).slice(0, 10).map(item => ({
                        title: item.querySelector('h3')?.innerText || '',
                        link: item.querySelector('a')?.href || '',
                        snippet: item.querySelector('.VwiC3b')?.innerText || ''
                    }));
                }
            """)
            return {"status": "success", "query": query, "results": results, "url": page.url}

        status, result = await self._call(_search)
        return result if status == "ok" else {"status": "error", "message": result}

    async def extract_content(self, session_id: str, selector: str = "body") -> dict:
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _extract():
            return page.evaluate(f"""() => {{
                const el = document.querySelector('{selector}');
                if (!el) return null;
                return {{ text: el.innerText, html: el.innerHTML }};
            }}""")

        status, result = await self._call(_extract)
        if status == "ok":
            return {"status": "success", "content": result, "url": page.url}
        return {"status": "error", "message": result}

    def list_sessions(self) -> list[dict]:
        return [{"session_id": s.session_id, "created_at": s.created_at, "last_active": s.last_active} for s in self._sessions.values()]


hermes_browser = HermesBrowserService()
