import asyncio
import time
from datetime import datetime, timezone
from typing import Optional


class NotificationService:
    def __init__(self):
        self._notifications: list[dict] = []
        self._max_notifications = 200
        self._listeners: list = []

    def add_notification(self, title: str, body: str, app: str = ""):
        entry = {
            "timestamp": time.time(),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "body": body,
            "app": app,
        }
        self._notifications.append(entry)
        if len(self._notifications) > self._max_notifications:
            self._notifications = self._notifications[-self._max_notifications:]

    def get_recent(self, limit: int = 20) -> list[dict]:
        return self._notifications[-limit:]

    def get_by_app(self, app: str, limit: int = 10) -> list[dict]:
        return [n for n in self._notifications if n.get("app", "").lower() == app.lower()][-limit:]

    def clear(self):
        self._notifications.clear()

    async def watch_windows_notifications(self):
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", """
                [void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
                $listener = New-Object System.Diagnostics.Eventing.Reader.EventLogWatcher
                """],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass


notification_service = NotificationService()
