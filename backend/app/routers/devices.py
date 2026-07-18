from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from app.models.database import get_db
from app.models.models import Device
import uuid

router = APIRouter()

CAPABILITY_MAP = {
    "android": ["screen-share", "voice", "camera", "adb"],
    "ios": ["screen-share", "voice", "camera"],
    "windows": ["screen-share", "voice", "ssh", "rdp"],
    "linux": ["screen-share", "voice", "ssh"],
    "cctv": ["rtsp", "camera"],
    "smart-home": ["voice"],
}


class DeviceCreate(BaseModel):
    name: str
    type: str
    platform: str
    ip: str = ""
    tailscale_ip: str = ""
    os_version: str = ""
    app_version: str = ""
    extra_data: dict = {}


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    battery: Optional[int] = None
    signal: Optional[str] = None
    capabilities: Optional[List[str]] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    extra_data: Optional[dict] = None


class HeartbeatData(BaseModel):
    battery: Optional[int] = None
    signal: Optional[str] = None
    status: str = "online"
    extra_data: Optional[dict] = None


def detect_capabilities(platform: str, custom: list = None) -> list:
    base = CAPABILITY_MAP.get(platform, ["voice"])
    if custom:
        return list(set(base + custom))
    return base


@router.get("/status/summary")
async def device_status_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device))
    devices = result.scalars().all()

    now = datetime.now(timezone.utc)
    online = 0
    offline = 0
    sleeping = 0

    for d in devices:
        if d.last_heartbeat:
            hb = d.last_heartbeat
            if hb.tzinfo is None:
                hb = hb.replace(tzinfo=timezone.utc)
            if (now - hb) > timedelta(minutes=5):
                d.status = "offline"
        if d.status == "online":
            online += 1
        elif d.status == "sleeping":
            sleeping += 1
        else:
            offline += 1

    return {
        "total": len(devices),
        "online": online,
        "offline": offline,
        "sleeping": sleeping,
    }


@router.get("/")
async def get_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Device).order_by(Device.last_seen.desc())
    )
    devices = result.scalars().all()
    now = datetime.now(timezone.utc)
    for device in devices:
        if device.last_heartbeat:
            hb = device.last_heartbeat
            if hb.tzinfo is None:
                hb = hb.replace(tzinfo=timezone.utc)
            elapsed = now - hb
            if elapsed > timedelta(minutes=5):
                device.status = "offline"
    return [_device_to_dict(d) for d in devices]


@router.get("/{device_id}")
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return _device_to_dict(device)


@router.post("/")
async def add_device(device: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device_id = str(uuid.uuid4())[:8]
    capabilities = detect_capabilities(device.platform)

    new_device = Device(
        id=device_id,
        user_id="default",
        name=device.name,
        type=device.type,
        platform=device.platform,
        ip=device.ip,
        tailscale_ip=device.tailscale_ip,
        capabilities=capabilities,
        status="online",
        last_seen=datetime.now(timezone.utc),
        last_heartbeat=datetime.now(timezone.utc),
        os_version=device.os_version,
        app_version=device.app_version,
        extra_data=device.extra_data,
    )
    db.add(new_device)
    await db.commit()
    return {"status": "added", "device_id": device_id, "capabilities": capabilities}


@router.put("/{device_id}")
async def update_device(
    device_id: str, update_data: DeviceUpdate, db: AsyncSession = Depends(get_db)
):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if update_dict:
        await db.execute(
            update(Device).where(Device.id == device_id).values(**update_dict)
        )
        await db.commit()

    device = await db.get(Device, device_id)
    return _device_to_dict(device)


@router.delete("/{device_id}")
async def remove_device(device_id: str, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()
    return {"status": "removed", "device_id": device_id}


@router.post("/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str, data: HeartbeatData, db: AsyncSession = Depends(get_db)
):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    values = {
        "last_heartbeat": datetime.now(timezone.utc),
        "last_seen": datetime.now(timezone.utc),
        "status": data.status,
    }
    if data.battery is not None:
        values["battery"] = data.battery
    if data.signal is not None:
        values["signal"] = data.signal
    if data.extra_data:
        values["extra_data"] = data.extra_data

    await db.execute(
        update(Device).where(Device.id == device_id).values(**values)
    )
    await db.commit()

    return {"status": "ok", "server_time": datetime.now(timezone.utc).isoformat()}


@router.post("/{device_id}/capabilities/detect")
async def detect_device_capabilities(
    device_id: str, db: AsyncSession = Depends(get_db)
):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    capabilities = detect_capabilities(device.platform, device.capabilities)
    await db.execute(
        update(Device)
        .where(Device.id == device_id)
        .values(capabilities=capabilities)
    )
    await db.commit()

    return {"device_id": device_id, "capabilities": capabilities}


def _device_to_dict(device: Device) -> dict:
    return {
        "id": device.id,
        "name": device.name,
        "type": device.type,
        "platform": device.platform,
        "ip": device.ip,
        "tailscale_ip": device.tailscale_ip,
        "capabilities": device.capabilities or [],
        "status": device.status,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "last_heartbeat": (
            device.last_heartbeat.isoformat() if device.last_heartbeat else None
        ),
        "battery": device.battery,
        "signal": device.signal,
        "os_version": device.os_version,
        "app_version": device.app_version,
        "metadata": device.extra_data or {},
    }
