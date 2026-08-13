"""Smart home skills: device control with offline state + optional MQTT.

Device state persists via ProfileStore (works without any hub). If an MQTT
service is available it publishes the command; otherwise the state is
recorded locally (useful for CCTV/presence devices too).
"""

import asyncio
from typing import Any, Dict

_STATE = {}  # module-level fallback when no profile store


def _store(ctx: Any):
    return getattr(ctx, "profile", None)


async def _set_device(ctx: Any, device: str, on: bool) -> None:
    value = "on" if on else "off"
    profile = _store(ctx)
    if profile is not None:
        profile.set_pref(f"device.{device}.state", value)
    else:
        _STATE[device] = value
    mqtt = getattr(ctx, "kernel", None) and ctx.kernel.get_service("mqtt")
    if mqtt is not None:
        try:
            await mqtt.publish(f"jarvis/device/{device}/set", value)
        except Exception:
            pass


async def smart_home_turn_on(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    device = params.get("device", "lights")
    await _set_device(ctx, device, True)
    return {"success": True, "narration": f"Turning on the {device}.",
            "type": "smart_home_action", "data": {"device": device, "state": "on"}}


async def smart_home_turn_off(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    device = params.get("device", "lights")
    await _set_device(ctx, device, False)
    return {"success": True, "narration": f"Turning off the {device}.",
            "type": "smart_home_action", "data": {"device": device, "state": "off"}}


async def smart_home_lock_door(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    await _set_device(ctx, "front_door_lock", True)
    return {"success": True, "narration": "Locking the front door.",
            "type": "smart_home_action", "data": {"device": "front_door_lock", "state": "locked"}}


async def smart_home_set_thermostat(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    temp = params.get("temperature") or params.get("temp") or ""
    if not temp:
        return {"success": False, "narration": "What temperature should I set?", "type": "smart_home_action"}
    profile = _store(ctx)
    if profile is not None:
        profile.set_pref("device.thermostat.temp", temp)
    else:
        _STATE["thermostat"] = temp
    return {"success": True, "narration": f"Setting the thermostat to {temp} degrees.",
            "type": "smart_home_action", "data": {"device": "thermostat", "temperature": temp}}


def register(reg) -> None:
    reg.skill("smart_home_turn_on", smart_home_turn_on, description="Turn a smart device on")
    reg.skill("smart_home_turn_off", smart_home_turn_off, description="Turn a smart device off")
    reg.skill("smart_home_lock_door", smart_home_lock_door, description="Lock the front door")
    reg.skill("smart_home_set_thermostat", smart_home_set_thermostat, description="Set thermostat temperature")
