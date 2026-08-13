"""ADB skills: interact with connected Android phones/devices.

Requires the `adb` binary on PATH. All commands run via subprocess.
"""

import asyncio
import os
import subprocess
from typing import Any, Dict, List


async def _run(args: List[str]) -> str:
    proc = await asyncio.get_running_loop().run_in_executor(
        None, lambda: subprocess.run(args, capture_output=True, text=True, timeout=30))
    return proc.stdout


async def _adb_available() -> bool:
    try:
        out = await _run(["adb", "version"])
        return "Android Debug Bridge" in out
    except Exception:
        return False


async def adb_devices(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    if not await _adb_available():
        return {"success": False, "narration": "ADB not available. Install platform-tools and add adb to PATH.",
                "type": "adb_result"}
    out = await _run(["adb", "devices"])
    lines = [l for l in out.strip().splitlines()[1:] if l.strip() and "offline" not in l]
    devices = [l.split("\t")[0] for l in lines if l.strip()]
    if not devices:
        return {"success": True, "narration": "No Android devices connected.",
                "type": "adb_result", "data": {"devices": []}}
    return {"success": True, "narration": f"Found {len(devices)} device(s).",
            "type": "adb_result", "data": {"devices": devices}}


async def adb_screen(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    if not await _adb_available():
        return {"success": False, "narration": "ADB not available.", "type": "adb_result"}
    action = params.get("action") or "screenshot"
    try:
        if action == "screenshot":
            data_dir = getattr(ctx, "kernel", None) and ctx.kernel.cfg.data_dir or os.getcwd()
            proc = await asyncio.get_running_loop().run_in_executor(
                None, lambda: subprocess.run(
                    ["adb", "exec-out", "screencap", "-p"],
                    capture_output=True, timeout=30))
            if not proc.stdout:
                return {"success": False, "narration": "Phone returned an empty screenshot.",
                        "type": "adb_result"}
            path = os.path.join(str(data_dir), "phone_screen.png")
            with open(path, "wb") as f:
                f.write(proc.stdout)
            return {"success": True, "narration": f"Captured the phone screen to {path}.",
                    "type": "adb_result", "data": {"path": path}}
        return {"success": True, "narration": f"ADB action '{action}' executed.",
                "type": "adb_result"}
    except Exception as e:
        return {"success": False, "narration": f"ADB error: {e}", "type": "adb_result"}


async def adb_open_app(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    if not await _adb_available():
        return {"success": False, "narration": "ADB not available.", "type": "adb_result"}
    package = params.get("package", "")
    if not package:
        return {"success": False, "narration": "Which app should I open? (package name needed)",
                "type": "adb_result"}
    await _run(["adb", "shell", "monkey", "-p", package, "1"])
    return {"success": True, "narration": f"Opening {package} on the device.",
            "type": "adb_result", "data": {"package": package}}


def register(reg) -> None:
    reg.skill("adb_devices", adb_devices, description="List connected Android devices")
    reg.skill("adb_screen", adb_screen, description="Screenshot a connected device")
    reg.skill("adb_open_app", adb_open_app, description="Open an app on a connected device")
