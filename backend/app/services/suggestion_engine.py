import time
from datetime import datetime, timezone
from typing import Optional


class SuggestionEngine:
    def __init__(self):
        self._suggestions: list[dict] = []
        self._dismissed: set[str] = set()
        self._last_suggestion_time = 0
        self._cooldown = 900
        self._rules: list[dict] = []
        self._time_patterns: dict[str, list[str]] = {}

        self._register_default_rules()

    def _register_default_rules(self):
        self._rules = [
            {
                "id": "disk_cleanup",
                "check": self._check_disk_cleanup,
                "cooldown": 3600,
                "last_fired": 0,
            },
            {
                "id": "work_break",
                "check": self._check_work_break,
                "cooldown": 7200,
                "last_fired": 0,
            },
            {
                "id": "high_cpu_suggestion",
                "check": self._check_high_cpu,
                "cooldown": 1800,
                "last_fired": 0,
            },
            {
                "id": "low_ram_suggestion",
                "check": self._check_low_ram,
                "cooldown": 1800,
                "last_fired": 0,
            },
        ]

    def get_suggestions(self) -> list[dict]:
        return [s for s in self._suggestions if s["id"] not in self._dismissed]

    def dismiss(self, suggestion_id: str):
        self._dismissed.add(suggestion_id)
        self._suggestions = [s for s in self._suggestions if s["id"] != suggestion_id]

    def add_time_pattern(self, hour: int, action: str):
        key = str(hour)
        if key not in self._time_patterns:
            self._time_patterns[key] = []
        if action not in self._time_patterns[key]:
            self._time_patterns[key].append(action)

    async def evaluate(self, monitoring_data: Optional[dict] = None,
                       activity_data: Optional[dict] = None,
                       screen_context: Optional[str] = None) -> list[dict]:
        now = time.time()
        if now - self._last_suggestion_time < self._cooldown:
            return self.get_suggestions()

        new_suggestions = []

        for rule in self._rules:
            if now - rule["last_fired"] < rule["cooldown"]:
                continue

            try:
                result = await rule["check"](monitoring_data, activity_data, screen_context)
                if result:
                    new_suggestions.append(result)
                    rule["last_fired"] = now
            except Exception:
                continue

        time_suggestions = self._check_time_patterns()
        new_suggestions.extend(time_suggestions)

        for s in new_suggestions:
            if not any(existing["id"] == s["id"] for existing in self._suggestions):
                self._suggestions.append(s)

        if new_suggestions:
            self._last_suggestion_time = now

        return self.get_suggestions()

    async def _check_disk_cleanup(self, monitoring_data, activity_data, screen_context) -> Optional[dict]:
        if not monitoring_data:
            return None
        disk_percent = monitoring_data.get("disk_percent", 0)
        if disk_percent > 90:
            return {
                "id": "disk_cleanup",
                "type": "system",
                "message": f"Disk is {disk_percent}% full. Shall I clean temporary files?",
                "action": "run_command",
                "action_params": {"command": "powershell -Command \"Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue\""},
                "priority": "high",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    async def _check_work_break(self, monitoring_data, activity_data, screen_context) -> Optional[dict]:
        if not monitoring_data:
            return None
        uptime = monitoring_data.get("uptime_hours", 0)
        if uptime > 4:
            return {
                "id": "work_break",
                "type": "wellness",
                "message": f"You've been working for {uptime:.0f} hours. Consider taking a break.",
                "priority": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    async def _check_high_cpu(self, monitoring_data, activity_data, screen_context) -> Optional[dict]:
        if not monitoring_data:
            return None
        cpu = monitoring_data.get("cpu_percent", 0)
        if cpu > 85:
            return {
                "id": "high_cpu_suggestion",
                "type": "system",
                "message": f"CPU usage is at {cpu}%. Would you like me to check which processes are using the most CPU?",
                "action": "get_top_processes",
                "priority": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    async def _check_low_ram(self, monitoring_data, activity_data, screen_context) -> Optional[dict]:
        if not monitoring_data:
            return None
        ram = monitoring_data.get("ram_percent", 0)
        if ram > 85:
            return {
                "id": "low_ram_suggestion",
                "type": "system",
                "message": f"RAM usage is at {ram}%. Closing unused apps may help performance.",
                "priority": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    def _check_time_patterns(self) -> list[dict]:
        suggestions = []
        hour = datetime.now().hour

        if str(hour) in self._time_patterns:
            actions = self._time_patterns[str(hour)]
            for action in actions[:1]:
                suggestions.append({
                    "id": f"time_pattern_{hour}",
                    "type": "pattern",
                    "message": f"I notice you usually {action} around this time. Shall I set that up?",
                    "priority": "low",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        return suggestions


suggestion_engine = SuggestionEngine()
