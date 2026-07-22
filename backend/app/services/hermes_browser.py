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
        self._pages: dict[str, Any] = {}  # session_id -> active page
        self._all_pages: dict[str, list] = {}  # session_id -> [page1, page2, ...]
        self._ready = threading.Event()
        self._init_error: Optional[str] = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=30)

    def _run(self):
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            try:
                self._browser = self._playwright.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                )
                print("Hermes Browser initialized (headless=False)")
            except Exception as e:
                print(f"[HERMES BROWSER] Headless=False failed, trying headless=True: {e}")
                try:
                    self._browser = self._playwright.chromium.launch(
                        headless=True,
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                    )
                    print("Hermes Browser initialized (headless=True)")
                except Exception as e2:
                    self._init_error = f"Failed to launch browser: {e2}"
                    print(f"[HERMES BROWSER] {self._init_error}")
                    self._ready.set()
                    return
            self._ready.set()
        except Exception as e:
            self._init_error = f"Playwright init failed: {e}"
            print(f"[HERMES BROWSER] {self._init_error}")
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

    def get_init_error(self) -> Optional[str]:
        return self._init_error

    def is_ready(self) -> bool:
        return self._browser is not None and self._init_error is None

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
        
        # Wait for browser to be ready
        max_wait = 30
        waited = 0
        while not _worker.is_ready() and waited < max_wait:
            await asyncio.sleep(0.5)
            waited += 0.5
        
        if not _worker.is_ready():
            error = _worker.get_init_error() or "Browser initialization timeout"
            raise Exception(f"Browser initialization failed: {error}")
        
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
            _worker._all_pages[session_id] = [page]
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
        _worker._all_pages.pop(session_id, None)
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
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                if is_youtube:
                    # Wait for YouTube to load - try multiple selectors
                    youtube_selectors = [
                        "ytd-search",
                        "ytd-video-renderer", 
                        "ytd-rich-grid-renderer",
                        "ytd-page-manager",
                        "#contents",
                        "ytd-app"
                    ]
                    for selector in youtube_selectors:
                        try:
                            page.wait_for_selector(selector, timeout=5000)
                            break
                        except Exception:
                            continue
                    
                    # Handle consent dialog - try multiple patterns
                    consent_selectors = [
                        "button:has-text('Accept all')",
                        "button:has-text('I agree')", 
                        "button:has-text('Reject all')",
                        "button[aria-label*='Accept']",
                        "button[aria-label*='accept']",
                        "ytd-button-renderer:has-text('Accept')",
                        "ytd-button-renderer:has-text('Agree')"
                    ]
                    for selector in consent_selectors:
                        try:
                            consent = page.locator(selector)
                            if consent.count() > 0:
                                consent.first.click(timeout=2000)
                                page.wait_for_load_state("domcontentloaded", timeout=3000)
                                break
                        except Exception:
                            continue
                    
                    # Additional wait for YouTube to settle
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                
                title = page.title()
                return {"status": "success", "url": page.url, "title": title, "status_code": response.status if response else None}
            except Exception as e:
                return {"status": "error", "message": f"Navigation failed: {str(e)}"}

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

    async def click_first_youtube_video(self, session_id: str) -> dict:
        """Navigate to YouTube search, then click the first video to play it."""
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _click_video():
            try:
                # Try multiple selectors for YouTube video links
                selectors = [
                    "ytd-video-renderer a#video-title",
                    "ytd-video-renderer a#thumbnail",
                    "ytd-rich-item-renderer a#video-title-link",
                    "a.yt-simple-endpoint[href*='/watch']",
                    "#contents ytd-video-renderer a",
                ]
                for sel in selectors:
                    try:
                        el = page.locator(sel)
                        if el.count() > 0:
                            el.first.click(timeout=10000)
                            page.wait_for_load_state("domcontentloaded", timeout=15000)
                            time.sleep(2)
                            return {"status": "success", "url": page.url, "title": page.title()}
                    except Exception:
                        continue
                
                return {"status": "error", "message": "No video found to click"}
            except Exception as e:
                return {"status": "error", "message": f"Failed to click video: {str(e)}"}

        status, result = await self._call(_click_video)
        return result

    async def get_page_summary(self, session_id: str) -> dict:
        """Get a summary of clickable elements and key content on the page."""
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}

        def _summary():
            try:
                return page.evaluate("""() => {
                    const summary = {title: document.title, url: location.href};
                    
                    // Get main headings
                    const headings = Array.from(document.querySelectorAll('h1, h2, h3')).slice(0, 5);
                    summary.headings = headings.map(h => h.innerText.trim()).filter(t => t.length > 0);
                    
                    // Get key links
                    const links = Array.from(document.querySelectorAll('a[href]')).slice(0, 10);
                    summary.key_links = links.map(a => ({
                        text: a.innerText.trim().substring(0, 50),
                        href: a.href
                    })).filter(l => l.text.length > 0);
                    
                    // Get buttons
                    const buttons = Array.from(document.querySelectorAll('button, [role="button"]')).slice(0, 10);
                    summary.buttons = buttons.map(b => b.innerText.trim()).filter(t => t.length > 0);
                    
                    // Get input fields
                    const inputs = Array.from(document.querySelectorAll('input, textarea')).slice(0, 5);
                    summary.inputs = inputs.map(i => ({
                        type: i.type,
                        placeholder: i.placeholder,
                        name: i.name
                    }));
                    
                    // Get page text summary (first 500 chars)
                    const bodyText = document.body?.innerText || '';
                    summary.text_preview = bodyText.substring(0, 500);
                    
                    return summary;
                }""")
            except Exception as e:
                return {"error": str(e)}

        status, result = await self._call(_summary)
        if status == "ok":
            return {"status": "success", "summary": result}
        return {"status": "error", "message": result}

    def list_sessions(self) -> list[dict]:
        return [{"session_id": s.session_id, "created_at": s.created_at, "last_active": s.last_active} for s in self._sessions.values()]

    def get_tab_info(self, session_id: str) -> dict:
        """Get info about all tabs in a session."""
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        context = _worker._contexts.get(session_id)
        if not context:
            return {"status": "error", "message": "Context not found"}
        
        pages = context.pages
        tabs = []
        active_page = _worker._pages.get(session_id)
        
        for i, page in enumerate(pages):
            try:
                title = page.title()
                url = page.url
            except Exception:
                title = "(loading)"
                url = "about:blank"
            
            tabs.append({
                "index": i,
                "title": title,
                "url": url,
                "is_active": page == active_page,
            })
        
        return {
            "status": "success",
            "session_id": session_id,
            "total_tabs": len(tabs),
            "active_tab_index": next((i for i, t in enumerate(tabs) if t["is_active"]), 0),
            "tabs": tabs,
        }

    async def get_all_tabs_info(self, session_id: str = None) -> dict:
        """Get info about all tabs across all sessions or a specific session."""
        if session_id:
            return self.get_tab_info(session_id)
        
        result = {}
        for sid in self._sessions:
            result[sid] = self.get_tab_info(sid)
        return {"status": "success", "sessions": result}

    def get_browser_state_for_llm(self) -> str:
        """Get a text summary of browser state for LLM context."""
        if not self._sessions:
            return "Browser: No active browser sessions."
        
        lines = ["Browser Status: Open"]
        
        for session_id, session in self._sessions.items():
            context = _worker._contexts.get(session_id)
            if not context:
                continue
            
            pages = context.pages
            active_page = _worker._pages.get(session_id)
            
            lines.append(f"\nSession '{session_id}': {len(pages)} tab(s) open")
            
            for i, page in enumerate(pages):
                try:
                    title = page.title()
                    url = page.url
                except Exception:
                    title = "(loading)"
                    url = "about:blank"
                
                prefix = "→" if page == active_page else " "
                lines.append(f"  {prefix} Tab {i+1}: {title} | {url}")
                
                # Add page context for active tab
                if page == active_page:
                    try:
                        # Get headings
                        headings = page.evaluate("() => Array.from(document.querySelectorAll('h1,h2,h3')).slice(0,3).map(h => h.innerText.trim()).filter(t => t)")
                        if headings:
                            lines.append(f"    Headings: {', '.join(headings)}")
                        
                        # Get visible buttons/links for navigation
                        elements = page.evaluate("""() => {
                            const items = [];
                            document.querySelectorAll('a, button, [role="button"]').forEach(el => {
                                const text = el.innerText?.trim();
                                if (text && text.length > 0 && text.length < 40) items.push(text);
                            });
                            return [...new Set(items)].slice(0, 8);
                        }""")
                        if elements:
                            lines.append(f"    Clickable: {', '.join(elements)}")
                        
                        # Get input fields
                        inputs = page.evaluate("""() => {
                            return Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea')).slice(0, 3).map(i => ({
                                placeholder: i.placeholder || i.name || i.type,
                                type: i.type
                            }));
                        }""")
                        if inputs:
                            input_descs = [f"{i.get('placeholder', i.get('type', 'field'))}" for i in inputs]
                            lines.append(f"    Inputs: {', '.join(input_descs)}")
                    except Exception:
                        pass
        
        return "\n".join(lines)

    def get_current_tab_info(self, session_id: str) -> dict:
        """Get info about the currently active tab."""
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        page = self._get_page(session_id)
        if not page:
            return {"status": "error", "message": "Page not found"}
        
        try:
            title = page.title()
            url = page.url
        except Exception:
            title = "(loading)"
            url = "about:blank"
        
        context = _worker._contexts.get(session_id)
        total_tabs = len(context.pages) if context else 1
        active_index = 0
        if context:
            for i, p in enumerate(context.pages):
                if p == page:
                    active_index = i
                    break
        
        return {
            "status": "success",
            "session_id": session_id,
            "title": title,
            "url": url,
            "tab_index": active_index,
            "total_tabs": total_tabs,
        }

    async def new_tab(self, session_id: str, url: str = "about:blank") -> dict:
        """Open a new tab in the session."""
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        context = _worker._contexts.get(session_id)
        if not context:
            return {"status": "error", "message": "Context not found"}
        
        def _new_tab():
            page = context.new_page()
            if url != "about:blank":
                if not url.startswith(("http://", "https://")):
                    url_with_protocol = "https://" + url
                else:
                    url_with_protocol = url
                page.goto(url_with_protocol, wait_until="domcontentloaded", timeout=30000)
            
            _worker._pages[session_id] = page
            _worker._all_pages.setdefault(session_id, []).append(page)
            
            try:
                title = page.title()
                page_url = page.url
            except Exception:
                title = "(loading)"
                page_url = url
            
            return {"status": "success", "title": title, "url": page_url}
        
        status, result = await self._call(_new_tab)
        return result if status == "ok" else {"status": "error", "message": result}

    async def switch_tab(self, session_id: str, tab_index: int) -> dict:
        """Switch to a specific tab by index."""
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        context = _worker._contexts.get(session_id)
        if not context:
            return {"status": "error", "message": "Context not found"}
        
        pages = context.pages
        if tab_index < 0 or tab_index >= len(pages):
            return {"status": "error", "message": f"Invalid tab index. Valid range: 0-{len(pages)-1}"}
        
        page = pages[tab_index]
        _worker._pages[session_id] = page
        
        try:
            title = page.title()
            url = page.url
        except Exception:
            title = "(loading)"
            url = "about:blank"
        
        return {"status": "success", "title": title, "url": url, "tab_index": tab_index}

    async def close_tab(self, session_id: str, tab_index: int = None) -> dict:
        """Close a specific tab or the active tab."""
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        context = _worker._contexts.get(session_id)
        if not context:
            return {"status": "error", "message": "Context not found"}
        
        pages = context.pages
        if len(pages) <= 1:
            return {"status": "error", "message": "Cannot close the last tab"}
        
        if tab_index is None:
            active_page = _worker._pages.get(session_id)
            for i, p in enumerate(pages):
                if p == active_page:
                    tab_index = i
                    break
            if tab_index is None:
                tab_index = 0
        
        if tab_index < 0 or tab_index >= len(pages):
            return {"status": "error", "message": f"Invalid tab index. Valid range: 0-{len(pages)-1}"}
        
        def _close_tab():
            page_to_close = pages[tab_index]
            page_to_close.close()
            
            remaining = context.pages
            if remaining:
                new_active = min(tab_index, len(remaining) - 1)
                _worker._pages[session_id] = remaining[new_active]
            
            return {"status": "success", "closed_tab_index": tab_index, "remaining_tabs": len(context.pages)}
        
        status, result = await self._call(_close_tab)
        return result if status == "ok" else {"status": "error", "message": result}


hermes_browser = HermesBrowserService()
