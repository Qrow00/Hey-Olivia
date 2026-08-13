"""System skills: time/date/health, OS power/volume/brightness, personality."""

import asyncio
import datetime
import os
import platform
import subprocess
import time
import ctypes
from typing import Any, Dict, Optional

_PROCESS_START = time.time()


def _os_type() -> str:
    return platform.system().lower()


async def _safe_shell(cmd: list) -> Optional[int]:
    try:
        return await asyncio.get_running_loop().run_in_executor(
            None, lambda: subprocess.call(cmd))
    except Exception:
        return None


async def info_time(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    now = datetime.datetime.now()
    return {"success": True, "narration": f"The time is {now.strftime('%I:%M %p')}.",
            "type": "info_response", "data": {"time": now.isoformat()}}


async def info_date(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    now = datetime.datetime.now()
    return {"success": True,
            "narration": f"Today is {now.strftime('%A, %B %d, %Y')}.",
            "type": "info_response", "data": {"date": now.isoformat()}}


async def info_health(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    sliders = ctx.personality.sliders() if getattr(ctx, "personality", None) else {}
    return {"success": True,
            "narration": "All systems nominal. Personality sliders engaged.",
            "type": "info_response", "data": {"personality": sliders}}


async def info_uptime(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    seconds = int(time.time() - _PROCESS_START)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return {"success": True,
            "narration": f"I have been online for {h} hours, {m} minutes, and {s} seconds.",
            "type": "info_response",
            "data": {"uptime_seconds": seconds, "uptime_hms": f"{h}:{m:02d}:{s:02d}"}}


async def info_weather(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    return {"success": False,
            "narration": "Weather requires a configured API key (weather.provider).",
            "type": "info_response"}


async def system_shutdown(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    if not params.get("confirm"):
        return {"success": False,
                "narration": "I need confirmation: say 'yes, shut down' to proceed.",
                "type": "system_action"}
    if _os_type() == "windows":
        os.system("shutdown /s /t 5")
    else:
        await _safe_shell(["shutdown", "-h", "now"])
    return {"success": True, "narration": "Shutting down the system in 5 seconds.",
            "type": "system_action"}


async def system_restart(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    if not params.get("confirm"):
        return {"success": False,
                "narration": "I need confirmation: say 'yes, restart' to proceed.",
                "type": "system_action"}
    if _os_type() == "windows":
        os.system("shutdown /r /t 5")
    else:
        await _safe_shell(["shutdown", "-r", "now"])
    return {"success": True, "narration": "Restarting in 5 seconds.", "type": "system_action"}


async def system_sleep(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    if _os_type() == "windows":
        ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
    else:
        await _safe_shell(["systemctl", "suspend"])
    return {"success": True, "narration": "Putting the system to sleep.", "type": "system_action"}


async def system_lock(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    if _os_type() == "windows":
        ctypes.windll.user32.LockWorkStation()
        return {"success": True, "narration": "Screen locked.", "type": "system_action"}
    return {"success": False, "narration": "Lock not supported on this OS.",
            "type": "system_action"}


async def system_volume(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    direction = params.get("amount", "")
    if _os_type() == "windows":
        import subprocess as sp
        try:
            code = 0xAF if direction == "up" else 0xAE
            ctypes.windll.user32.keybd_event(code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(code, 0, 2, 0)
            return {"success": True, "narration": f"Volume {direction}.", "type": "system_action"}
        except Exception as e:
            return {"success": False, "narration": f"Volume error: {e}", "type": "system_action"}
    return {"success": False, "narration": "Volume control not supported here.",
            "type": "system_action"}


async def system_brightness(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    direction = params.get("amount", "")
    if _os_type() == "windows":
        try:
            import wmi
            from ctypes import windll
            w = wmi.WMI(namespace="root\\WMI")
            for b in w.WmiMonitorBrightnessMethods():
                cur = b.WmiGetBrightness().CurrentBrightness
                b.WmiSetBrightness(0, max(0, min(100, cur + (10 if direction == "up" else -10))))
            return {"success": True, "narration": f"Brightness {direction}.", "type": "system_action"}
        except Exception:
            return {"success": False,
                    "narration": "Brightness requires the 'wmi' package (pip install wmi).",
                    "type": "system_action"}
    return {"success": False, "narration": "Brightness not supported here.",
            "type": "system_action"}


async def system_mute(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    return await system_volume({**params, "amount": "down"}, ctx)


async def set_personality(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    p = getattr(ctx, "personality", None)
    if p is None:
        return {"success": False, "narration": "Personality service unavailable.",
                "type": "personality_action"}
    trait = params.get("trait", "")
    direction = params.get("direction", "more")
    if p.adjust(trait, direction):
        return {"success": True,
                "narration": f"Personality adjusted: {trait} is now {direction}.",
                "type": "personality_action", "data": {"sliders": p.sliders()}}
    return {"success": False,
            "narration": f"I don't have a '{trait}' slider. Try humor, sarcasm, warmth, energy, formality, or curiosity.",
            "type": "personality_action"}


def register(reg) -> None:
    reg.skill("info_time", info_time, description="Report the current time")
    reg.skill("info_date", info_date, description="Report today's date")
    reg.skill("info_health", info_health, description="Report agent status")
    reg.skill("info_uptime", info_uptime, description="Report how long JARVIS has been running")
    reg.skill("info_weather", info_weather, description="Report weather (needs API key)")
    reg.skill("system_shutdown", system_shutdown, description="Shut down the computer (needs confirm)")
    reg.skill("system_restart", system_restart, description="Restart the computer (needs confirm)")
    reg.skill("system_sleep", system_sleep, description="Put the computer to sleep")
    reg.skill("system_lock", system_lock, description="Lock the workstation")
    reg.skill("system_volume_up", lambda p, c: system_volume({**p, "amount": "up"}, c), description="Raise volume")
    reg.skill("system_volume_down", lambda p, c: system_volume({**p, "amount": "down"}, c), description="Lower volume")
    reg.skill("system_brightness_up", lambda p, c: system_brightness({**p, "amount": "up"}, c), description="Brighten display")
    reg.skill("system_brightness_down", lambda p, c: system_brightness({**p, "amount": "down"}, c), description="Dim display")
    reg.skill("system_mute", system_mute, description="Mute the volume")
    reg.skill("set_personality", set_personality, description="Adjust emotional sliders by voice")
