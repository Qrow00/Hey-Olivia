import asyncio
import time
import subprocess
import re
from datetime import datetime, timezone
from typing import Optional
import psutil


class ActivityLogger:
    def __init__(self):
        self._log: list[dict] = []
        self._max_entries = 5000
        self._polling = False
        self._poll_interval = 60
        self._active_window_history: list[dict] = []
        self._process_snapshots: list[dict] = []
        self._listeners: list = []

    def get_recent_activity(self, limit: int = 20) -> list[dict]:
        return self._log[-limit:]

    def get_active_window_history(self, minutes: int = 60) -> list[dict]:
        cutoff = time.time() - (minutes * 60)
        return [w for w in self._active_window_history if w.get("timestamp", 0) > cutoff]

    def get_top_processes(self, limit: int = 10) -> list[dict]:
        if not self._process_snapshots:
            return []
        latest = self._process_snapshots[-1]
        return latest.get("processes", [])[:limit]

    def get_process_history(self, minutes: int = 30) -> list[dict]:
        cutoff = time.time() - (minutes * 60)
        return [p for p in self._process_snapshots if p.get("timestamp", 0) > cutoff]

    def add_listener(self, callback):
        self._listeners.append(callback)

    def _log_entry(self, category: str, detail: str, extra: Optional[dict] = None):
        entry = {
            "timestamp": time.time(),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "detail": detail,
            **(extra or {}),
        }
        self._log.append(entry)
        if len(self._log) > self._max_entries:
            self._log = self._log[-self._max_entries:]
        return entry

    def _get_active_window_windows(self) -> Optional[dict]:
        try:
            script = """
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class WinAPI {
                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();
                [DllImport("user32.dll", CharSet = CharSet.Auto)]
                public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
                [DllImport("user32.dll")]
                public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
            }
"@
            $hwnd = [WinAPI]::GetForegroundWindow()
            $sb = New-Object System.Text.StringBuilder 256
            [WinAPI]::GetWindowText($hwnd, $sb, 256) | Out-Null
            $pid = 0
            [WinAPI]::GetWindowThreadProcessId($hwnd, [ref]$pid) | Out-Null
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Output "$($proc.Name)|$($sb.ToString())|$pid"
            }
            """
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.stdout.strip():
                parts = result.stdout.strip().split("|", 2)
                if len(parts) >= 2:
                    return {
                        "process": parts[0],
                        "title": parts[1],
                        "pid": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                    }
        except Exception:
            pass
        return None

    def _get_top_processes_windows(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 Name, Id, CPU, WorkingSet64 | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW
            )
            import json
            raw = json.loads(result.stdout)
            if isinstance(raw, dict):
                raw = [raw]
            processes = []
            for p in raw:
                processes.append({
                    "name": p.get("Name", ""),
                    "pid": p.get("Id", 0),
                    "cpu_seconds": round(p.get("CPU", 0), 1),
                    "memory_mb": round(p.get("WorkingSet64", 0) / (1024 * 1024), 1),
                })
            return sorted(processes, key=lambda x: x["memory_mb"], reverse=True)
        except Exception:
            return []

    def _collect_snapshot(self) -> dict:
        window = self._get_active_window_windows()
        processes = self._get_top_processes_windows()

        snapshot = {
            "timestamp": time.time(),
            "active_window": window,
            "processes": processes,
        }

        if window:
            self._active_window_history.append({
                "timestamp": time.time(),
                **window,
            })
            if len(self._active_window_history) > 2000:
                self._active_window_history = self._active_window_history[-2000:]

        self._process_snapshots.append(snapshot)
        if len(self._process_snapshots) > 500:
            self._process_snapshots = self._process_snapshots[-500:]

        return snapshot

    async def _poll_loop(self):
        while self._polling:
            try:
                snapshot = await asyncio.to_thread(self._collect_snapshot)

                window = snapshot.get("active_window")
                if window:
                    self._log_entry(
                        "window",
                        f"{window['process']}: {window['title']}",
                        {"process": window["process"], "pid": window.get("pid", 0)},
                    )

            except Exception as e:
                print(f"[ACTIVITY] Poll error: {e}")

            await asyncio.sleep(self._poll_interval)

    async def start_polling(self):
        if self._polling:
            return
        self._polling = True
        asyncio.create_task(self._poll_loop())
        print("[ACTIVITY] Started activity logging")

    async def stop_polling(self):
        self._polling = False
        print("[ACTIVITY] Stopped activity logging")


activity_logger = ActivityLogger()
