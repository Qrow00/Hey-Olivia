import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class DeviceType(str, Enum):
    LIGHT = "light"
    SWITCH = "switch"
    THERMOSTAT = "thermostat"
    LOCK = "lock"
    FAN = "fan"
    CURTAIN = "curtain"
    SENSOR = "sensor"
    PLUG = "plug"
    SPEAKER = "speaker"
    CAMERA = "camera"


class Protocol(str, Enum):
    MQTT = "mqtt"
    HTTP = "http"
    HUE = "hue"
    TASMOTA = "tasmota"
    SHelly = "shelly"


@dataclass
class SmartDevice:
    id: str
    name: str
    type: DeviceType
    protocol: Protocol
    ip: str = ""
    topic: str = ""
    room: str = ""
    is_online: bool = False
    is_on: bool = False
    brightness: int = 100
    color: str = "#ffffff"
    temperature: float = 22.0
    humidity: float = 0
    battery: int = 100
    state: dict = field(default_factory=dict)
    capabilities: list = field(default_factory=list)
    last_update: float = 0


class SmartHomeService:
    def __init__(self):
        self.devices: dict[str, SmartDevice] = {}
        self._mqtt_client = None
        self._http_clients: dict[str, str] = {}
        self._status_callbacks: list[Callable] = []
        self._automation_rules: list[dict] = []

    async def initialize_mqtt(self, broker: str, port: int = 1883, username: str = "", password: str = ""):
        try:
            import paho.mqtt.client as mqtt

            self._mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            if username:
                self._mqtt_client.username_pw_set(username, password)

            self._mqtt_client.on_connect = self._on_mqtt_connect
            self._mqtt_client.on_message = self._on_mqtt_message

            self._mqtt_client.connect(broker, port, 60)
            self._mqtt_client.loop_start()
            return {"status": "connected", "broker": broker}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        print(f"MQTT connected with result code {rc}")
        for device in self.devices.values():
            if device.protocol == Protocol.MQTT and device.topic:
                client.subscribe(device.topic + "/#")

    def _on_mqtt_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split("/")
            payload = json.loads(msg.payload.decode())

            for device in self.devices.values():
                if device.topic and msg.topic.startswith(device.topic):
                    device.state.update(payload)
                    device.last_update = time.time()
                    device.is_online = True

                    if "state" in payload:
                        device.is_on = payload["state"].lower() in ["on", "true", "1"]
                    if "brightness" in payload:
                        device.brightness = int(payload["brightness"])
                    if "color" in payload:
                        device.color = payload["color"]
                    if "temperature" in payload:
                        device.temperature = float(payload["temperature"])
                    if "humidity" in payload:
                        device.humidity = float(payload["humidity"])

                    self._notify_status(device)
                    break
        except Exception as e:
            print(f"MQTT message error: {e}")

    def _notify_status(self, device: SmartDevice):
        for callback in self._status_callbacks:
            try:
                callback(device)
            except:
                pass

    def on_device_status(self, callback: Callable):
        self._status_callbacks.append(callback)

    async def add_device(self, device: SmartDevice) -> dict:
        self.devices[device.id] = device

        if device.protocol == Protocol.MQTT and device.topic and self._mqtt_client:
            self._mqtt_client.subscribe(device.topic + "/#")

        return {"status": "added", "device_id": device.id}

    async def remove_device(self, device_id: str) -> dict:
        device = self.devices.pop(device_id, None)
        if device and device.protocol == Protocol.MQTT and device.topic and self._mqtt_client:
            self._mqtt_client.unsubscribe(device.topic + "/#")
        return {"status": "removed", "device_id": device_id}

    async def control_device(self, device_id: str, command: dict) -> dict:
        device = self.devices.get(device_id)
        if not device:
            return {"status": "error", "message": "Device not found"}

        action = command.get("action", "")
        params = command.get("params", {})

        if device.protocol == Protocol.MQTT:
            return await self._control_mqtt(device, action, params)
        elif device.protocol == Protocol.HTTP:
            return await self._control_http(device, action, params)
        elif device.protocol == Protocol.TASMOTA:
            return await self._control_tasmota(device, action, params)
        elif device.protocol == Protocol.Shelly:
            return await self._control_shelly(device, action, params)

        return {"status": "error", "message": "Unsupported protocol"}

    async def _control_mqtt(self, device: SmartDevice, action: str, params: dict) -> dict:
        if not self._mqtt_client:
            return {"status": "error", "message": "MQTT not connected"}

        payload = {}

        if action == "on":
            device.is_on = True
            payload = {"state": "ON"}
        elif action == "off":
            device.is_on = False
            payload = {"state": "OFF"}
        elif action == "toggle":
            device.is_on = not device.is_on
            payload = {"state": "ON" if device.is_on else "OFF"}
        elif action == "set_brightness":
            device.brightness = params.get("brightness", 100)
            payload = {"brightness": device.brightness}
        elif action == "set_color":
            device.color = params.get("color", "#ffffff")
            payload = {"color": device.color}
        elif action == "set_temperature":
            device.temperature = params.get("temperature", 22.0)
            payload = {"temperature": device.temperature}
        elif action == "set_state":
            device.state.update(params)
            payload = params

        if payload and device.topic:
            self._mqtt_client.publish(
                f"{device.topic}/set",
                json.dumps(payload),
                retain=True
            )

        device.last_update = time.time()
        self._notify_status(device)

        return {"status": "success", "device_id": device.id, "action": action}

    async def _control_http(self, device: SmartDevice, action: str, params: dict) -> dict:
        import httpx

        url = f"http://{device.ip}"
        payload = {"action": action, **params}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{url}/api/control", json=payload, timeout=5.0)
                if response.status_code == 200:
                    device.state.update(response.json())
                    device.last_update = time.time()
                    self._notify_status(device)
                    return {"status": "success", "device_id": device.id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return {"status": "error", "message": "HTTP request failed"}

    async def _control_tasmota(self, device: SmartDevice, action: str, params: dict) -> dict:
        import httpx

        url = f"http://{device.ip}"

        try:
            async with httpx.AsyncClient() as client:
                if action in ["on", "off"]:
                    response = await client.get(f"{url}/cm?cmnd=Power%20{'On' if action == 'on' else 'Off'}")
                elif action == "set_brightness":
                    brightness = params.get("brightness", 100)
                    response = await client.get(f"{url}/cm?cmnd=Dimmer%20{brightness}")
                elif action == "set_color":
                    color = params.get("color", "FFFFFF")
                    response = await client.get(f"{url}/cm?cmnd=Color%20{color}")
                else:
                    return {"status": "error", "message": "Unknown Tasmota action"}

                if response.status_code == 200:
                    device.is_on = action in ["on", "toggle"] or (action == "off" and not device.is_on)
                    device.last_update = time.time()
                    self._notify_status(device)
                    return {"status": "success", "device_id": device.id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return {"status": "error", "message": "Tasmota request failed"}

    async def _control_shelly(self, device: SmartDevice, action: str, params: dict) -> dict:
        import httpx

        url = f"http://{device.ip}"

        try:
            async with httpx.AsyncClient() as client:
                if action in ["on", "off"]:
                    response = await client.get(f"{url}/relay/0?turn={'on' if action == 'on' else 'off'}")
                elif action == "set_brightness":
                    brightness = params.get("brightness", 100)
                    response = client.get(f"{url}/dimmer/0?brightness={brightness}")
                else:
                    return {"status": "error", "message": "Unknown Shelly action"}

                if response.status_code == 200:
                    device.is_on = action in ["on", "toggle"] or (action == "off" and not device.is_on)
                    device.last_update = time.time()
                    self._notify_status(device)
                    return {"status": "success", "device_id": device.id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return {"status": "error", "message": "Shelly request failed"}

    def get_device(self, device_id: str) -> Optional[SmartDevice]:
        return self.devices.get(device_id)

    def get_all_devices(self) -> list[dict]:
        return [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type.value if isinstance(d.type, DeviceType) else d.type,
                "protocol": d.protocol.value if isinstance(d.protocol, Protocol) else d.protocol,
                "ip": d.ip,
                "topic": d.topic,
                "room": d.room,
                "is_online": d.is_online,
                "is_on": d.is_on,
                "brightness": d.brightness,
                "color": d.color,
                "temperature": d.temperature,
                "humidity": d.humidity,
                "battery": d.battery,
                "state": d.state,
                "capabilities": d.capabilities,
                "last_update": d.last_update,
            }
            for d in self.devices.values()
        ]

    def get_devices_by_room(self, room: str) -> list[dict]:
        return [d for d in self.get_all_devices() if d["room"] == room]

    def get_rooms(self) -> list[str]:
        return list(set(d.room for d in self.devices.values() if d.room))

    async def execute_scene(self, scene: dict) -> dict:
        results = []
        for action in scene.get("actions", []):
            device_id = action.get("device_id")
            command = action.get("command", {})
            result = await self.control_device(device_id, command)
            results.append(result)
        return {"status": "executed", "results": results}


smart_home_service = SmartHomeService()
