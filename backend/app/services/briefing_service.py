import asyncio
from datetime import datetime, timezone
from typing import Optional
from app.services.weather_service import weather_service
from app.services.news_service import news_service
from app.services.monitoring_service import monitoring_service
from app.services.voice_service import voice_service
from app.services.voice_profile_service import voice_profile_service
from app.services.personality_service import personality_service


class BriefingService:
    def __init__(self):
        self.sources = {
            "weather": True,
            "system": True,
            "news": True,
            "smart_home": True,
            "calendar": False,
        }
        self._last_briefing: Optional[str] = None

    def configure(self, sources: dict):
        for key, val in sources.items():
            if key in self.sources:
                self.sources[key] = val

    def get_config(self) -> dict:
        return self.sources.copy()

    async def generate_briefing(self, include_tts: bool = True) -> dict:
        parts = []
        tasks = []

        if self.sources["weather"]:
            tasks.append(("weather", self._get_weather()))

        if self.sources["system"]:
            tasks.append(("system", self._get_system()))

        if self.sources["news"]:
            tasks.append(("news", self._get_news()))

        if self.sources["smart_home"]:
            tasks.append(("smart_home", self._get_smart_home()))

        if self.sources["calendar"]:
            tasks.append(("calendar", self._get_calendar()))

        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for (name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                continue
            if result:
                parts.append(result)

        greeting = self._get_time_greeting()
        full_text = f"{greeting} " + " ".join(parts)

        tts_audio = None
        if include_tts:
            try:
                profile = voice_profile_service.get_active_profile()
                tts_audio = await voice_service.text_to_speech(
                    full_text,
                    voice=profile.voice,
                    rate=profile.rate,
                    pitch=profile.pitch,
                )
            except Exception:
                pass

        self._last_briefing = full_text

        return {
            "text": full_text,
            "parts": parts,
            "tts_audio": tts_audio,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_weather(self) -> str:
        try:
            return await weather_service.get_summary()
        except Exception:
            return ""

    async def _get_system(self) -> str:
        try:
            snapshot = monitoring_service.get_snapshot()
            cpu = snapshot.get("cpu_percent", 0)
            ram = snapshot.get("ram_percent", 0)
            disk = snapshot.get("disk_percent", 0)
            uptime = snapshot.get("uptime_hours", 0)

            parts = [f"System is running for {uptime:.0f} hours."]
            parts.append(f"CPU at {cpu}%, RAM at {ram}%, disk at {disk}%.")

            if cpu > 80:
                parts.append("CPU is running hot.")
            if disk > 85:
                parts.append("Disk space getting low.")

            return " ".join(parts)
        except Exception:
            return ""

    async def _get_news(self) -> str:
        try:
            return await news_service.get_summary(limit=3)
        except Exception:
            return ""

    async def _get_smart_home(self) -> str:
        try:
            from app.services.smart_home_service import smart_home_service
            devices = smart_home_service.get_all_devices() if hasattr(smart_home_service, 'get_all_devices') else []
            if not devices:
                return ""
            online = sum(1 for d in devices if d.get("status") == "online")
            return f"Smart home: {online} of {len(devices)} devices online."
        except Exception:
            return ""

    async def _get_calendar(self) -> str:
        return "Calendar integration not yet configured."

    def _get_time_greeting(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning."
        elif 12 <= hour < 17:
            return "Good afternoon."
        elif 17 <= hour < 21:
            return "Good evening."
        else:
            return "Good night."


briefing_service = BriefingService()
