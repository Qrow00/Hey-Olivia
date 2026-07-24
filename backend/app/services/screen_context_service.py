import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from app.services.ocr_service import ocr_service


class ScreenContextService:
    def __init__(self):
        self._polling = False
        self._poll_interval = 120
        self._history: list[dict] = []
        self._max_history = 100
        self._latest_summary: Optional[str] = None

    def get_latest(self) -> Optional[str]:
        return self._latest_summary

    def get_history(self, limit: int = 10) -> list[dict]:
        return self._history[-limit:]

    async def capture_and_summarize(self, prompt: str = "") -> dict:
        try:
            result = await ocr_service.ocr_screenshot(prompt=prompt or "Summarize what's currently on screen in 2-3 sentences.")
            summary = result.get("result", {}).get("text", "") if isinstance(result.get("result"), dict) else str(result.get("result", ""))

            entry = {
                "timestamp": time.time(),
                "timestamp_iso": datetime.now(timezone.utc).isoformat(),
                "summary": summary,
            }

            self._latest_summary = summary
            self._history.append(entry)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

            return {"status": "success", "summary": summary}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _poll_loop(self):
        while self._polling:
            try:
                await self.capture_and_summarize()
            except Exception:
                pass
            await asyncio.sleep(self._poll_interval)

    async def start_polling(self):
        if self._polling:
            return
        self._polling = True
        asyncio.create_task(self._poll_loop())
        print("[SCREEN CONTEXT] Started polling")

    async def stop_polling(self):
        self._polling = False
        print("[SCREEN CONTEXT] Stopped polling")


screen_context_service = ScreenContextService()
