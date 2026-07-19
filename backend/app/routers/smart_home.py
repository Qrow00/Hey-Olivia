from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.smart_home_service import smart_home_service, SmartDevice, DeviceType, Protocol
import uuid

router = APIRouter()


class SmartDeviceCreate(BaseModel):
    name: str
    type: str = "light"
    protocol: str = "mqtt"
    ip: Optional[str] = ""
    topic: Optional[str] = ""
    room: Optional[str] = ""
    capabilities: Optional[List[str]] = []


class DeviceControl(BaseModel):
    action: str
    params: Optional[Dict[str, Any]] = {}


class SceneCreate(BaseModel):
    name: str
    actions: List[Dict[str, Any]]


class MQTTConfig(BaseModel):
    broker: str
    port: int = 1883
    username: Optional[str] = ""
    password: Optional[str] = ""


@router.get("/")
async def get_devices():
    return smart_home_service.get_all_devices()


@router.get("/rooms")
async def get_rooms():
    return smart_home_service.get_rooms()


@router.get("/rooms/{room}")
async def get_devices_by_room(room: str):
    return smart_home_service.get_devices_by_room(room)


@router.get("/{device_id}")
async def get_device(device_id: str):
    device = smart_home_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {
        "id": device.id,
        "name": device.name,
        "type": device.type.value if isinstance(device.type, DeviceType) else device.type,
        "protocol": device.protocol.value if isinstance(device.protocol, Protocol) else device.protocol,
        "ip": device.ip,
        "topic": device.topic,
        "room": device.room,
        "is_online": device.is_online,
        "is_on": device.is_on,
        "brightness": device.brightness,
        "color": device.color,
        "temperature": device.temperature,
        "humidity": device.humidity,
        "battery": device.battery,
        "state": device.state,
        "capabilities": device.capabilities,
        "last_update": device.last_update,
    }


@router.post("/")
async def add_device(device: SmartDeviceCreate):
    device_id = str(uuid.uuid4())[:8]
    smart_device = SmartDevice(
        id=device_id,
        name=device.name,
        type=DeviceType(device.type),
        protocol=Protocol(device.protocol),
        ip=device.ip,
        topic=device.topic,
        room=device.room,
        capabilities=device.capabilities,
    )
    result = await smart_home_service.add_device(smart_device)
    return result


@router.delete("/{device_id}")
async def delete_device(device_id: str):
    result = await smart_home_service.remove_device(device_id)
    return result


@router.post("/{device_id}/control")
async def control_device(device_id: str, control: DeviceControl):
    result = await smart_home_service.control_device(device_id, {
        "action": control.action,
        "params": control.params,
    })
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{device_id}/on")
async def turn_on(device_id: str):
    result = await smart_home_service.control_device(device_id, {"action": "on"})
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{device_id}/off")
async def turn_off(device_id: str):
    result = await smart_home_service.control_device(device_id, {"action": "off"})
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{device_id}/toggle")
async def toggle(device_id: str):
    result = await smart_home_service.control_device(device_id, {"action": "toggle"})
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{device_id}/brightness")
async def set_brightness(device_id: str, brightness: int):
    result = await smart_home_service.control_device(device_id, {
        "action": "set_brightness",
        "params": {"brightness": brightness},
    })
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{device_id}/color")
async def set_color(device_id: str, color: str):
    result = await smart_home_service.control_device(device_id, {
        "action": "set_color",
        "params": {"color": color},
    })
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/scenes")
async def execute_scene(scene: SceneCreate):
    result = await smart_home_service.execute_scene({
        "name": scene.name,
        "actions": scene.actions,
    })
    return result


@router.post("/mqtt/connect")
async def connect_mqtt(config: MQTTConfig):
    result = await smart_home_service.initialize_mqtt(
        broker=config.broker,
        port=config.port,
        username=config.username,
        password=config.password,
    )
    return result
