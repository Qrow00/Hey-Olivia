"""System diagnostics: probe each subsystem and report which are functional."""
import asyncio
import importlib.util
import subprocess

import psutil

from app.services.thermal_logger_service import thermal_logger_service


class DiagnosticsService:
    def __init__(self):
        self._check_timeout = 6.0

    async def run(self) -> dict:
        checks = await asyncio.gather(
            *[self._timed(name, coro) for name, coro in self._all_checks()]
        )
        passed = sum(1 for c in checks if c["status"] in ("ok", "warn"))
        applicable = sum(1 for c in checks if c["status"] != "skip")
        report = {
            "status": "success",
            "checks": checks,
            "failed": [c["name"] for c in checks if c["status"] == "fail"],
            "summary": f"{passed} of {applicable} checks passed",
            "message": f"Diagnostics complete: {passed} of {applicable} checks passed.",
        }
        return report

    async def _timed(self, name: str, coro) -> dict:
        try:
            return await asyncio.wait_for(coro, timeout=self._check_timeout)
        except asyncio.TimeoutError:
            return {"name": name, "status": "fail", "detail": "timed out"}
        except Exception as e:
            return {"name": name, "status": "fail", "detail": f"{type(e).__name__}: {e}"}

    def _all_checks(self) -> list:
        return [
            ("CPU", self._check_cpu()),
            ("RAM", self._check_ram()),
            ("Disk", self._check_disk()),
            ("GPU", self._check_gpu()),
            ("Battery", self._check_battery()),
            ("LLM (Ollama)", self._check_ollama()),
            ("Speech-to-text (Whisper)", self._check_stt()),
            ("Text-to-speech (edge-tts)", self._check_tts()),
            ("Wake word", self._check_wake_word()),
            ("Internet", self._check_internet()),
            ("Tailscale", self._check_tailscale()),
            ("Browser", self._check_browser()),
            ("Cameras", self._check_cameras()),
            ("Smart home", self._check_smart_home()),
            ("Thermal logger", self._check_thermal_logger()),
        ]

    async def _check_thermal_logger(self):
        if not await asyncio.to_thread(thermal_logger_service.is_running):
            await asyncio.to_thread(thermal_logger_service.start)
        for _ in range(8):
            if await asyncio.to_thread(thermal_logger_service.is_running):
                return {"name": "Thermal logger", "status": "ok", "detail": "running"}
            await asyncio.sleep(0.5)
        return {"name": "Thermal logger", "status": "fail", "detail": "not running"}

    async def _check_cpu(self):
        value = await asyncio.to_thread(psutil.cpu_percent, 0.5)
        return {"name": "CPU", "status": "ok" if value < 90 else "warn", "detail": f"{value}% load"}

    async def _check_ram(self):
        mem = await asyncio.to_thread(psutil.virtual_memory)
        return {"name": "RAM", "status": "ok" if mem.percent < 85 else "warn", "detail": f"{mem.percent}% used"}

    async def _check_disk(self):
        disk = await asyncio.to_thread(psutil.disk_usage, "/")
        return {"name": "Disk", "status": "ok" if disk.percent < 90 else "warn", "detail": f"{disk.percent}% used"}

    def _nvidia_smi(self) -> str:
        try:
            return subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            ).stdout.strip()
        except Exception:
            return ""

    async def _check_gpu(self):
        out = await asyncio.to_thread(self._nvidia_smi)
        if not out:
            return {"name": "GPU", "status": "fail", "detail": "nvidia-smi unavailable"}
        parts = [p.strip() for p in out.split(",")]
        try:
            load, temp = float(parts[1]), float(parts[2])
        except (ValueError, IndexError):
            return {"name": "GPU", "status": "fail", "detail": out}
        status = "ok" if temp < 85 and load < 95 else "warn"
        return {"name": "GPU", "status": status, "detail": f"{parts[0]}, {load}% load, {temp}C"}

    async def _check_battery(self):
        bat = await asyncio.to_thread(psutil.sensors_battery)
        if bat is None:
            return {"name": "Battery", "status": "skip", "detail": "no battery detected"}
        status = "ok" if bat.power_plugged or bat.percent > 20 else "warn"
        ac = "AC" if bat.power_plugged else "battery"
        return {"name": "Battery", "status": status, "detail": f"{bat.percent}%, on {ac}"}

    async def _check_ollama(self):
        import httpx
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code != 200:
                return {"name": "LLM (Ollama)", "status": "fail", "detail": f"HTTP {resp.status_code}"}
            models = [m.get("name", "") for m in resp.json().get("models", [])]
        except Exception as e:
            return {"name": "LLM (Ollama)", "status": "fail", "detail": f"{type(e).__name__}: {e}"}
        if not models:
            return {"name": "LLM (Ollama)", "status": "fail", "detail": "no models found"}
        status = "ok" if any(m.startswith("llama3.2") for m in models) else "warn"
        return {"name": "LLM (Ollama)", "status": status, "detail": ", ".join(models[:4])}

    @staticmethod
    def _importable(name: str) -> bool:
        return importlib.util.find_spec(name) is not None

    async def _check_stt(self):
        if not self._importable("whisper"):
            return {"name": "Speech-to-text (Whisper)", "status": "fail", "detail": "whisper not installed"}
        from app.services.voice_service import voice_service
        detail = "loaded" if getattr(voice_service, "stt_model", None) else "installed"
        return {"name": "Speech-to-text (Whisper)", "status": "ok", "detail": detail}

    async def _check_tts(self):
        if self._importable("edge_tts"):
            return {"name": "Text-to-speech (edge-tts)", "status": "ok", "detail": "installed"}
        return {"name": "Text-to-speech (edge-tts)", "status": "fail", "detail": "edge_tts not installed"}

    async def _check_wake_word(self):
        if self._importable("openwakeword"):
            return {"name": "Wake word", "status": "ok", "detail": "installed"}
        return {"name": "Wake word", "status": "fail", "detail": "openwakeword not installed"}

    async def _check_internet(self):
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={"latitude": 0, "longitude": 0, "current_weather": True},
                )
            if resp.status_code == 200:
                return {"name": "Internet", "status": "ok", "detail": "reachable"}
            return {"name": "Internet", "status": "fail", "detail": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"name": "Internet", "status": "fail", "detail": f"{type(e).__name__}: {e}"}

    async def _check_tailscale(self):
        from app.services.tailscale_service import tailscale_service
        try:
            ok = await tailscale_service.is_available()
            return {"name": "Tailscale", "status": "ok" if ok else "fail", "detail": "connected" if ok else "not available"}
        except Exception as e:
            return {"name": "Tailscale", "status": "fail", "detail": f"{type(e).__name__}: {e}"}

    async def _check_browser(self):
        from app.services import hermes_browser
        worker = hermes_browser._worker
        if worker.is_ready():
            return {"name": "Browser", "status": "ok", "detail": "ready"}
        if worker.get_init_error():
            return {"name": "Browser", "status": "fail", "detail": worker.get_init_error()}
        return {"name": "Browser", "status": "skip", "detail": "not initialized"}

    async def _check_cameras(self):
        from app.services.rtsp_service import rtsp_service
        cameras = rtsp_service.get_all_cameras()
        if not cameras:
            return {"name": "Cameras", "status": "skip", "detail": "no cameras configured"}
        online = sum(1 for c in cameras if c["is_online"])
        status = "ok" if online == len(cameras) else "warn"
        return {"name": "Cameras", "status": status, "detail": f"{online} of {len(cameras)} online"}

    async def _check_smart_home(self):
        from app.services.smart_home_service import smart_home_service
        if not smart_home_service.devices:
            return {"name": "Smart home", "status": "skip", "detail": "no smart devices configured"}
        client = smart_home_service._mqtt_client
        if client is None:
            return {"name": "Smart home", "status": "fail", "detail": "MQTT not initialized"}
        try:
            connected = await asyncio.to_thread(client.is_connected)
        except Exception as e:
            return {"name": "Smart home", "status": "fail", "detail": f"{type(e).__name__}: {e}"}
        return {"name": "Smart home", "status": "ok" if connected else "fail", "detail": "MQTT connected" if connected else "MQTT disconnected"}

    async def _check_thermal_logger(self):
        for _ in range(8):
            if await asyncio.to_thread(self._thermal_logger_running):
                return {"name": "Thermal logger", "status": "ok", "detail": "running"}
            await asyncio.sleep(0.5)
        return {"name": "Thermal logger", "status": "fail", "detail": "not running"}


diagnostics_service = DiagnosticsService()
