import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class HealthMetric:
    device_id: str
    metric: str
    value: float
    unit: str
    timestamp: float


@dataclass
class WearableDevice:
    id: str
    name: str
    type: str
    platform: str
    is_online: bool = False
    battery: int = 100
    firmware_version: str = ""
    last_sync: float = 0


@dataclass
class HealthSummary:
    heart_rate: Optional[dict] = None
    spo2: Optional[dict] = None
    steps: Optional[dict] = None
    sleep: Optional[dict] = None
    calories: Optional[dict] = None
    stress: Optional[dict] = None
    blood_pressure: Optional[dict] = None
    body_temperature: Optional[dict] = None


class WearableService:
    def __init__(self):
        self.devices: dict[str, WearableDevice] = {}
        self.health_history: dict[str, list[HealthMetric]] = {}
        self.subscribers: dict[str, list[str]] = {}
        self._health_cache: dict[str, HealthSummary] = {}

    async def register_device(self, device: WearableDevice) -> dict:
        self.devices[device.id] = device
        self.health_history[device.id] = []
        self._health_cache[device.id] = HealthSummary()
        return {"status": "registered", "device_id": device.id}

    async def unregister_device(self, device_id: str) -> dict:
        self.devices.pop(device_id, None)
        self.health_history.pop(device_id, None)
        self._health_cache.pop(device_id, None)
        return {"status": "unregistered", "device_id": device_id}

    def record_metric(self, device_id: str, metric: str, value: float, unit: str = ""):
        health = HealthMetric(
            device_id=device_id,
            metric=metric,
            value=value,
            unit=unit,
            timestamp=time.time(),
        )

        if device_id not in self.health_history:
            self.health_history[device_id] = []
        self.health_history[device_id].append(health)

        if len(self.health_history[device_id]) > 1000:
            self.health_history[device_id] = self.health_history[device_id][-500:]

        self._update_cache(device_id, metric, value, unit)

        if device_id in self.devices:
            self.devices[device_id].last_sync = time.time()
            self.devices[device_id].is_online = True

    def _update_cache(self, device_id: str, metric: str, value: float, unit: str):
        cache = self._health_cache.get(device_id)
        if not cache:
            return

        metric_data = {
            "current": value,
            "unit": unit,
            "timestamp": time.time(),
        }

        history = [
            m.value for m in self.health_history.get(device_id, [])
            if m.metric == metric
       ][-20:]

        if history:
            metric_data["avg"] = sum(history) / len(history)
            metric_data["min"] = min(history)
            metric_data["max"] = max(history)

        if metric == "heart_rate":
            cache.heart_rate = metric_data
        elif metric == "spo2":
            cache.spo2 = metric_data
        elif metric == "steps":
            metric_data["today_total"] = sum(
                m.value for m in self.health_history.get(device_id, [])
                if m.metric == "steps" and m.timestamp > self._get_today_start()
            )
            cache.steps = metric_data
        elif metric == "sleep":
            cache.sleep = metric_data
        elif metric == "calories":
            cache.calories = metric_data
        elif metric == "stress":
            cache.stress = metric_data
        elif metric == "blood_pressure":
            cache.blood_pressure = metric_data
        elif metric == "body_temperature":
            cache.body_temperature = metric_data

    def _get_today_start(self) -> float:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return today_start.timestamp()

    def get_health_summary(self, device_id: str) -> Optional[dict]:
        cache = self._health_cache.get(device_id)
        if not cache:
            return None

        return {
            "heart_rate": cache.heart_rate,
            "spo2": cache.spo2,
            "steps": cache.steps,
            "sleep": cache.sleep,
            "calories": cache.calories,
            "stress": cache.stress,
            "blood_pressure": cache.blood_pressure,
            "body_temperature": cache.body_temperature,
        }

    def get_health_history(self, device_id: str, metric: str = None, limit: int = 50) -> list[dict]:
        history = self.health_history.get(device_id, [])

        if metric:
            history = [m for m in history if m.metric == metric]

        return [
            {
                "metric": m.metric,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp,
            }
            for m in history[-limit:]
        ]

    def get_device(self, device_id: str) -> Optional[WearableDevice]:
        return self.devices.get(device_id)

    def get_all_devices(self) -> list[dict]:
        return [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "platform": d.platform,
                "is_online": d.is_online,
                "battery": d.battery,
                "firmware_version": d.firmware_version,
                "last_sync": d.last_sync,
                "health_summary": self.get_health_summary(d.id),
            }
            for d in self.devices.values()
        ]

    def subscribe(self, client_id: str, metrics: list[str]):
        self.subscribers[client_id] = metrics

    def unsubscribe(self, client_id: str):
        self.subscribers.pop(client_id, None)

    def get_subscribers(self) -> list[str]:
        return list(self.subscribers.keys())

    def check_alerts(self, device_id: str) -> list[dict]:
        alerts = []
        cache = self._health_cache.get(device_id)
        if not cache:
            return alerts

        if cache.heart_rate:
            hr = cache.heart_rate["current"]
            if hr > 120:
                alerts.append({
                    "type": "high_heart_rate",
                    "severity": "warning",
                    "message": f"Heart rate elevated: {hr} bpm",
                    "value": hr,
                })
            elif hr < 50:
                alerts.append({
                    "type": "low_heart_rate",
                    "severity": "warning",
                    "message": f"Heart rate low: {hr} bpm",
                    "value": hr,
                })

        if cache.spo2:
            spo2 = cache.spo2["current"]
            if spo2 < 90:
                alerts.append({
                    "type": "low_spo2",
                    "severity": "critical",
                    "message": f"Blood oxygen low: {spo2}%",
                    "value": spo2,
                })

        if cache.stress:
            stress = cache.stress["current"]
            if stress > 75:
                alerts.append({
                    "type": "high_stress",
                    "severity": "info",
                    "message": f"Stress level high: {stress}",
                    "value": stress,
                })

        return alerts


wearable_service = WearableService()
