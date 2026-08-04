import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from app.services.monitoring_service import monitoring_service


class AlertEngine:
    def __init__(self):
        self._rules: list[dict] = []
        self._alert_history: list[dict] = []
        self._max_history = 200
        self._notification_callback = None
        self._active = False

        self._add_default_rules()

    def _add_default_rules(self):
        self._rules = [
            {
                "id": "high_cpu",
                "metric": "cpu_percent",
                "condition": ">=",
                "threshold": 90,
                "severity": "warning",
                "message": "CPU usage is critically high at {value}%",
                "cooldown": 300,
                "enabled": True,
            },
            {
                "id": "high_ram",
                "metric": "ram_percent",
                "condition": ">=",
                "threshold": 85,
                "severity": "warning",
                "message": "RAM usage is high at {value}%",
                "cooldown": 300,
                "enabled": True,
            },
            {
                "id": "disk_full",
                "metric": "disk_percent",
                "condition": ">=",
                "threshold": 90,
                "severity": "critical",
                "message": "Disk is {value}% full — consider cleaning up",
                "cooldown": 3600,
                "enabled": True,
            },
            {
                "id": "gpu_overheat",
                "metric": "gpu_temp",
                "condition": ">=",
                "threshold": 85,
                "severity": "critical",
                "message": "GPU temperature is {value}°C — overheating risk",
                "cooldown": 300,
                "enabled": True,
            },
            {
                "id": "gpu_max_load",
                "metric": "gpu_load",
                "condition": ">=",
                "threshold": 98,
                "severity": "warning",
                "message": "GPU load at {value}% — thermal throttling possible",
                "cooldown": 600,
                "enabled": True,
            },
            {
                "id": "vram_high",
                "metric": "gpu_memory_used",
                "condition": ">=",
                "threshold": 3072,
                "severity": "warning",
                "message": "VRAM usage at {value} MB — over the 3 GB budget",
                "cooldown": 300,
                "enabled": True,
            },
        ]

    def set_notification_callback(self, callback):
        self._notification_callback = callback

    def add_rule(self, rule: dict):
        self._rules.append(rule)

    def remove_rule(self, rule_id: str):
        self._rules = [r for r in self._rules if r["id"] != rule_id]

    def get_rules(self) -> list[dict]:
        return self._rules.copy()

    def toggle_rule(self, rule_id: str, enabled: bool):
        for rule in self._rules:
            if rule["id"] == rule_id:
                rule["enabled"] = enabled
                break

    def get_alert_history(self, limit: int = 20) -> list[dict]:
        return self._alert_history[-limit:]

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        ops = {
            ">=": lambda v, t: v >= t,
            "<=": lambda v, t: v <= t,
            ">": lambda v, t: v > t,
            "<": lambda v, t: v < t,
            "==": lambda v, t: abs(v - t) < 0.01,
        }
        return ops.get(condition, lambda v, t: False)(value, threshold)

    async def evaluate(self, snapshot: dict) -> list[dict]:
        triggered = []
        now = time.time()

        for rule in self._rules:
            if not rule.get("enabled", True):
                continue

            metric = rule["metric"]
            value = snapshot.get(metric)
            if value is None:
                continue

            if not self._evaluate_condition(value, rule["condition"], rule["threshold"]):
                continue

            cooldown = rule.get("cooldown", 300)
            last_fired = rule.get("_last_fired", 0)
            if now - last_fired < cooldown:
                continue

            alert = {
                "rule_id": rule["id"],
                "metric": metric,
                "severity": rule["severity"],
                "message": rule["message"].format(value=value),
                "value": value,
                "threshold": rule["threshold"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            triggered.append(alert)
            rule["_last_fired"] = now

            self._alert_history.append(alert)
            if len(self._alert_history) > self._max_history:
                self._alert_history = self._alert_history[-self._max_history:]

        if triggered and self._notification_callback:
            for alert in triggered:
                try:
                    await self._notification_callback(alert)
                except Exception:
                    pass

        return triggered

    def _on_monitoring_alert(self, alert: dict):
        pass


alert_engine = AlertEngine()
