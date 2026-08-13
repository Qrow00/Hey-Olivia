"""Media skills: play/pause/skip media and YouTube lookup/launch.

YouTube is opened via the default browser (no heavy deps). OS media keys
use ctypes on Windows (guarded). 
"""

import ctypes
import webbrowser
from typing import Any, Dict
from urllib.parse import quote

_MEDIA_KEYS = {"play_pause": 0xB3, "next": 0xB0, "previous": 0xB1, "stop": 0xB2}


def _send_media_key(code: int) -> bool:
    try:
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)
        return True
    except Exception:
        return False


async def browser_youtube(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    query = params.get("query", "").strip()
    if query:
        url = f"https://www.youtube.com/results?search_query={quote(query)}"
        label = f"searching YouTube for '{query}'"
    else:
        url = "https://www.youtube.com"
        label = "opening YouTube"
    try:
        webbrowser.open(url)
        return {"success": True, "narration": f"Now {label}.", "type": "media_action",
                "data": {"url": url}}
    except Exception as e:
        return {"success": False, "narration": f"Could not open browser: {e}",
                "type": "media_action", "data": {"url": url}}


async def media_play(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    ok = _send_media_key(_MEDIA_KEYS["play_pause"])
    return {"success": True if ok else False,
            "narration": "Playing media." if ok else "Media keys unavailable on this platform.",
            "type": "media_action"}


async def media_pause(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    ok = _send_media_key(_MEDIA_KEYS["play_pause"])
    return {"success": True if ok else False,
            "narration": "Paused." if ok else "Media keys unavailable on this platform.",
            "type": "media_action"}


async def media_next(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    ok = _send_media_key(_MEDIA_KEYS["next"])
    return {"success": True if ok else False,
            "narration": "Skipping to the next track." if ok else "Media keys unavailable.",
            "type": "media_action"}


async def media_previous(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    ok = _send_media_key(_MEDIA_KEYS["previous"])
    return {"success": True if ok else False,
            "narration": "Going back." if ok else "Media keys unavailable.",
            "type": "media_action"}


async def media_stop(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    ok = _send_media_key(_MEDIA_KEYS["stop"])
    return {"success": True if ok else False,
            "narration": "Stopped." if ok else "Media keys unavailable.",
            "type": "media_action"}


async def browser_youtube_open(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    return await browser_youtube({}, ctx)


def register(reg) -> None:
    reg.skill("browser_youtube", browser_youtube, description="Search or open YouTube")
    reg.skill("browser_youtube_open", browser_youtube_open,
              description="Open YouTube (alias intent)")
    reg.skill("media_play", media_play, description="Play or resume media")
    reg.skill("media_pause", media_pause, description="Pause media")
    reg.skill("media_next", media_next, description="Next track")
    reg.skill("media_previous", media_previous, description="Previous track")
    reg.skill("media_stop", media_stop, description="Stop media")
