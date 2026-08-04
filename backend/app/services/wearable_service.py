import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select, func, delete
from app.models.database import async_session
from app.models.models import WearableDeviceDB, HealthMetricDB


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
        self.subscribers: dict[str, list[str]] = {}
        self._health_cache: dict[str, HealthSummary] = {}

    async def load_from_db(self):
        async with async_session() as session:
            result = await session.execute(select(WearableDeviceDB))
            devices = result.scalars().all()
            for d in devices:
                self._health_cache[d.id] = HealthSummary()
                metrics_result = await session.execute(
                    select(HealthMetricDB)
                    .where(HealthMetricDB.device_id == d.id)
                    .order_by(HealthMetricDB.timestamp.desc())
                    .limit(20)
                )
                for m in reversed(metrics_result.scalars().all()):
                    self._update_cache(d.id, m.metric, m.value, m.unit)

    async def register_device(self, device: WearableDevice, user_id: str = "default") -> dict:
        async with async_session() as session:
            existing = await session.get(WearableDeviceDB, device.id)
            if existing:
                existing.name = device.name
                existing.type = device.type
                existing.platform = device.platform
                existing.is_online = device.is_online
                existing.battery = device.battery
                existing.firmware_version = device.firmware_version
                existing.last_sync = (
                    datetime.fromtimestamp(device.last_sync, tz=timezone.utc)
                    if device.last_sync else None
                )
            else:
                session.add(WearableDeviceDB(
                    id=device.id,
                    user_id=user_id,
                    name=device.name,
                    type=device.type,
                    platform=device.platform,
                    is_online=device.is_online,
                    battery=device.battery,
                    firmware_version=device.firmware_version,
                    last_sync=(
                        datetime.fromtimestamp(device.last_sync, tz=timezone.utc)
                        if device.last_sync else None
                    ),
                ))
            await session.commit()

        self._health_cache.setdefault(device.id, HealthSummary())
        return {"status": "registered", "device_id": device.id}

    async def unregister_device(self, device_id: str) -> dict:
        async with async_session() as session:
            await session.execute(
                delete(HealthMetricDB).where(HealthMetricDB.device_id == device_id)
            )
            await session.execute(
                delete(WearableDeviceDB).where(WearableDeviceDB.id == device_id)
            )
            await session.commit()
        self._health_cache.pop(device_id, None)
        return {"status": "unregistered", "device_id": device_id}

    async def record_metric(self, device_id: str, metric: str, value: float, unit: str = ""):
        async with async_session() as session:
            session.add(HealthMetricDB(
                device_id=device_id,
                metric=metric,
                value=value,
                unit=unit,
            ))

            stmt = (
                select(HealthMetricDB)
                .where(HealthMetricDB.device_id == device_id)
                .order_by(HealthMetricDB.timestamp.desc())
                .offset(1000)
            )
            overflow = (await session.execute(stmt)).scalars().all()
            for old in overflow:
                await session.delete(old)

            device_db = await session.get(WearableDeviceDB, device_id)
            if device_db:
                device_db.last_sync = datetime.now(timezone.utc)
                device_db.is_online = True

            await session.commit()

        self._update_cache(device_id, metric, value, unit)

    async def record_metrics_batch(self, device_id: str, metrics: list[dict]):
        now = datetime.now(timezone.utc)
        async with async_session() as session:
            for m in metrics:
                session.add(HealthMetricDB(
                    device_id=device_id,
                    metric=m["metric"],
                    value=m["value"],
                    unit=m.get("unit", ""),
                ))
            device_db = await session.get(WearableDeviceDB, device_id)
            if device_db:
                device_db.last_sync = now
                device_db.is_online = True
            await session.commit()

        for m in metrics:
            self._update_cache(device_id, m["metric"], m["value"], m.get("unit", ""))

    def _update_cache(self, device_id: str, metric: str, value: float, unit: str):
        cache = self._health_cache.get(device_id)
        if not cache:
            cache = HealthSummary()
            self._health_cache[device_id] = cache

        metric_data = {
            "current": value,
            "unit": unit,
            "timestamp": time.time(),
        }

        if metric == "heart_rate":
            cache.heart_rate = metric_data
        elif metric == "spo2":
            cache.spo2 = metric_data
        elif metric == "steps":
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

    async def get_health_history(self, device_id: str, metric: str = None, limit: int = 50) -> list[dict]:
        async with async_session() as session:
            q = (
                select(HealthMetricDB)
                .where(HealthMetricDB.device_id == device_id)
            )
            if metric:
                q = q.where(HealthMetricDB.metric == metric)
            q = q.order_by(HealthMetricDB.timestamp.desc()).limit(limit)
            result = await session.execute(q)
            return [
                {
                    "metric": m.metric,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.replace(tzinfo=timezone.utc).timestamp(),
                }
                for m in reversed(result.scalars().all())
            ]

    async def get_device(self, device_id: str) -> Optional[dict]:
        async with async_session() as session:
            d = await session.get(WearableDeviceDB, device_id)
            if not d:
                return None
            return {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "platform": d.platform,
                "is_online": d.is_online,
                "battery": d.battery,
                "firmware_version": d.firmware_version,
                "last_sync": d.last_sync.timestamp() if d.last_sync else 0,
                "health_summary": self.get_health_summary(d.id),
            }

    async def get_all_devices(self, user_id: str = None) -> list[dict]:
        async with async_session() as session:
            q = select(WearableDeviceDB)
            if user_id:
                q = q.where(WearableDeviceDB.user_id == user_id)
            result = await session.execute(q)
            devices = result.scalars().all()
            return [
                {
                    "id": d.id,
                    "name": d.name,
                    "type": d.type,
                    "platform": d.platform,
                    "is_online": d.is_online,
                    "battery": d.battery,
                    "firmware_version": d.firmware_version,
                    "last_sync": d.last_sync.timestamp() if d.last_sync else 0,
                    "health_summary": self.get_health_summary(d.id),
                }
                for d in devices
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
