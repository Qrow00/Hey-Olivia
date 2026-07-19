from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.wearable_service import wearable_service, WearableDevice
import uuid

router = APIRouter()


class WearableCreate(BaseModel):
    name: str
    type: str = "smartwatch"
    platform: str = "android"
    firmware_version: Optional[str] = ""


class HealthUpdate(BaseModel):
    metric: str
    value: float
    unit: Optional[str] = ""


@router.get("/")
async def get_wearables():
    return wearable_service.get_all_devices()


@router.get("/{device_id}")
async def get_wearable(device_id: str):
    device = wearable_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Wearable not found")
    return {
        "id": device.id,
        "name": device.name,
        "type": device.type,
        "platform": device.platform,
        "is_online": device.is_online,
        "battery": device.battery,
        "firmware_version": device.firmware_version,
        "last_sync": device.last_sync,
        "health_summary": wearable_service.get_health_summary(device.id),
    }


@router.post("/")
async def register_wearable(wearable: WearableCreate):
    device_id = str(uuid.uuid4())[:8]
    device = WearableDevice(
        id=device_id,
        name=wearable.name,
        type=wearable.type,
        platform=wearable.platform,
        firmware_version=wearable.firmware_version,
    )
    result = await wearable_service.register_device(device)
    return result


@router.delete("/{device_id}")
async def unregister_wearable(device_id: str):
    result = await wearable_service.unregister_device(device_id)
    return result


@router.post("/{device_id}/health")
async def update_health(device_id: str, update: HealthUpdate):
    device = wearable_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Wearable not found")

    wearable_service.record_metric(device_id, update.metric, update.value, update.unit)

    alerts = wearable_service.check_alerts(device_id)

    return {
        "status": "recorded",
        "device_id": device_id,
        "metric": update.metric,
        "value": update.value,
        "alerts": alerts,
    }


@router.get("/{device_id}/health")
async def get_health_summary(device_id: str):
    summary = wearable_service.get_health_summary(device_id)
    if not summary:
        raise HTTPException(status_code=404, detail="No health data")
    return {"device_id": device_id, "health": summary}


@router.get("/{device_id}/health/history")
async def get_health_history(device_id: str, metric: Optional[str] = None, limit: int = 50):
    history = wearable_service.get_health_history(device_id, metric, limit)
    return {"device_id": device_id, "history": history}


@router.get("/{device_id}/alerts")
async def get_alerts(device_id: str):
    alerts = wearable_service.check_alerts(device_id)
    return {"device_id": device_id, "alerts": alerts}
