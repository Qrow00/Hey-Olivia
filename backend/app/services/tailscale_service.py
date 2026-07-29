import asyncio
import platform
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone


def _run(args: list[str]) -> str | None:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


class TailscaleService:
    def __init__(self):
        self._cached_ip = None
        self._cached_available = None
        self._last_check = datetime.min.replace(tzinfo=timezone.utc)
        self._cache_seconds = 60

    @property
    def _tailscale_bin(self) -> str:
        if platform.system() == "Windows":
            candidates = [
                shutil.which("tailscale"),
                "C:\\Program Files\\Tailscale\\tailscale.exe",
                "C:\\Program Files (x86)\\Tailscale\\tailscale.exe",
            ]
            for c in candidates:
                if c and Path(c).exists():
                    return c
            return "tailscale"
        return shutil.which("tailscale") or "tailscale"

    async def detect_ip(self) -> str | None:
        now = datetime.now(timezone.utc)
        if self._cached_ip and (now - self._last_check).total_seconds() < self._cache_seconds:
            return self._cached_ip
        ip = await asyncio.to_thread(_run, [self._tailscale_bin, "ip", "-4"])
        self._cached_ip = ip if ip else None
        self._cached_available = self._cached_ip is not None
        self._last_check = now
        return self._cached_ip

    async def is_available(self) -> bool:
        ip = await self.detect_ip()
        return ip is not None

    async def get_status(self) -> dict:
        ip = await self.detect_ip()
        return {
            "available": ip is not None,
            "ip": ip,
        }

    async def get_hostname(self) -> str | None:
        out = await asyncio.to_thread(_run, [self._tailscale_bin, "status"])
        if not out:
            return None
        for line in out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0] == self._cached_ip:
                return parts[1]
        return None


tailscale_service = TailscaleService()
