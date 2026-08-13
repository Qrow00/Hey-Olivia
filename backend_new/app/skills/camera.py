"""Camera/CCTV skills: capture photos, view/analyze camera feeds, identify people.

opencv-python is optional. Without it, camera capture degrades gracefully.
Face recognition reuses the vision service when enabled.
"""

import asyncio
import os
from typing import Any, Dict


def _try_cv2():
    try:
        import cv2
        return cv2
    except Exception:
        return None


def _vision(ctx: Any):
    return getattr(ctx, "kernel", None) and ctx.kernel.get_service("face_recognizer")


async def camera_capture(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    cv2 = _try_cv2()
    if cv2 is None:
        return {"success": False,
                "narration": "Camera unavailable: install opencv-python (pip install opencv-python).",
                "type": "camera_result"}
    index = int(params.get("camera_index", 0))
    data_dir = getattr(ctx, "kernel", None) and ctx.kernel.cfg.data_dir or os.getcwd()
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            return {"success": False, "narration": f"No camera found at index {index}.",
                    "type": "camera_result"}
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return {"success": False, "narration": "Could not capture a frame.",
                    "type": "camera_result"}
        path = os.path.join(str(data_dir), "capture.jpg")
        cv2.imwrite(path, frame)
        return {"success": True, "narration": f"Photo captured to {path}.",
                "type": "camera_result", "data": {"path": path}}
    except Exception as e:
        return {"success": False, "narration": f"Camera error: {e}", "type": "camera_result"}


async def vision_identify(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    rec = _vision(ctx)
    if rec is None:
        return {"success": False, "narration": "Vision service is not enabled (JARVIS_SERVICES=vision).",
                "type": "vision_result", "faces": []}
    frame = params.get("image") or params.get("path") or None
    return await rec.recognize(frame)


async def cctv_view(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    streams = []
    profile = getattr(ctx, "profile", None)
    if profile is not None:
        streams = profile.get_pref("cctv.streams", []) or []
    if not streams:
        return {"success": False,
                "narration": "No CCTV streams configured. Set prefs: cctv.streams (list of RTSP/HTTP URLs).",
                "type": "cctv_result"}
    import webbrowser
    opened = 0
    for url in streams[:3]:
        try:
            webbrowser.open(url)
            opened += 1
        except Exception:
            pass
    return {"success": opened > 0,
            "narration": f"Opened {opened} camera feed(s)." if opened else "Could not open camera feeds.",
            "type": "cctv_result", "data": {"streams": streams}}


async def cctv_analyze(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    rec = _vision(ctx)
    if rec is None:
        return {"success": False, "narration": "Vision service not enabled (JARVIS_SERVICES=vision).",
                "type": "cctv_result"}
    frame = params.get("image") or params.get("path") or params.get("url") or None
    result = await rec.recognize(frame)
    return {**result, "type": "cctv_result"}


def register(reg) -> None:
    reg.skill("camera_capture", camera_capture, description="Take a photo with a connected camera")
    reg.skill("vision_identify", vision_identify, description="Identify a person in an image")
    reg.skill("cctv_view", cctv_view, description="Open CCTV/security camera feeds")
    reg.skill("cctv_analyze", cctv_analyze, description="Analyze camera feed for people")
