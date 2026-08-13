"""WebSocket gateway for J.A.R.V.I.S. V4.

Transport-compatible with V3 (text_command/voice_chunk/settings_update/
plugin_control/switch_profile/knowledge_search) plus new types:
voice_audio, personality_update, teach_example, feedback.
"""

import base64
import asyncio
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.api.processor import process_text


class WSConnectionManager:
    """Track active WebSocket clients and broadcast messages."""

    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def send(self, ws: WebSocket, message: Dict[str, Any]) -> None:
        try:
            await ws.send_json(message)
        except Exception:
            self.disconnect(ws)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for ws in list(self.active):
            await self.send(ws, message)


manager = WSConnectionManager()


async def ws_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    app = websocket.app
    ctx = app.state.ctx
    if ctx is not None and getattr(ctx.cfg, "access_token", ""):
        provided = websocket.query_params.get("token", "")
        if provided != ctx.cfg.access_token:
            await manager.send(websocket, {"type": "error", "message": "Unauthorized"})
            await websocket.close(code=4401)
            manager.disconnect(websocket)
            return
    print("WebSocket client connected")

    try:
        while True:
            data = await websocket.receive_json()
            try:
                await handle_message(websocket, data)
            except Exception as e:
                print(f"[WS] handler error: {e}")
                try:
                    await manager.send(websocket, {"type": "error", "message": f"Handler error: {e}"})
                except Exception:
                    pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket client disconnected")


async def handle_message(websocket: WebSocket, data: Dict[str, Any]) -> None:
    """Route one inbound WS message to its handler."""
    app = websocket.app
    ctx = app.state.ctx
    msg_type = data.get("type", "")

    if msg_type in ("text_command", "voice_command"):
        text = data.get("text", "")
        if ctx is None or not text:
            await manager.send(websocket, {"type": "error", "message": "Not ready or empty."})
            return
        result = await process_text(app, text)
        await manager.send(websocket, {"type": "command_result", **result})

    elif msg_type == "voice_chunk":
        await manager.send(websocket, {
            "type": "voice_status", "is_listening": True,
            "wake_detected": False, "simulated": True,
        })

    elif msg_type == "voice_audio":
        await handle_voice_audio(websocket, data)

    elif msg_type == "personality_update":
        if ctx is not None:
            sliders = ctx.personality.set_many(data.get("settings", {}))
            await manager.send(websocket, {"type": "personality_state", "sliders": sliders})

    elif msg_type == "personality_get":
        if ctx is not None:
            await manager.send(websocket, {"type": "personality_state",
                                           "sliders": ctx.personality.sliders()})

    elif msg_type == "teach_example":
        if ctx is not None:
            ok = await ctx.nlu.teach(data.get("text", ""), data.get("intent", ""))
            await manager.send(websocket, {"type": "teach_result", "success": ok})

    elif msg_type == "feedback":
        store = ctx.kernel.get_service("feedback") if ctx else None
        if store is not None:
            await store.record(data.get("text", ""), data.get("intent", "chat"),
                               data.get("rating", "good"), data.get("note", ""),
                               data.get("correction", ""))
            await manager.send(websocket, {"type": "feedback_result", "success": True})

    elif msg_type == "settings_update":
        if ctx is not None and ctx.state_store is not None:
            profile = data.get("profile", ctx.cfg.profile)
            for key, value in data.get("settings", {}).items():
                ctx.state_store.set(profile, f"settings.{key}", value)
            await manager.send(websocket, {"type": "settings_updated", "success": True})

    elif msg_type == "plugin_control":
        if ctx is not None:
            ctx.kernel.registry.set_enabled(data.get("name", ""), data.get("enabled", False))
            await manager.send(websocket, {"type": "plugin_status", "success": True})

    elif msg_type == "knowledge_search":
        vs = ctx.kernel.get_service("vectors") if ctx else None
        if vs is not None and vs.count() > 0:
            await manager.send(websocket, {"type": "knowledge_results",
                                           "count": vs.count(), "success": True})
        else:
            await manager.send(websocket, {"type": "knowledge_results",
                                           "results": [], "success": True})

    else:
        await manager.send(websocket, {
            "type": "error", "code": "unknown_message",
            "message": f"Unknown message type: {msg_type}",
        })


async def handle_voice_audio(websocket: WebSocket, data: Dict[str, Any]) -> None:
    """voice_audio: base64 raw PCM -> wake word -> STT -> process -> TTS."""
    app = websocket.app
    ctx = app.state.ctx
    if ctx is None:
        await manager.send(websocket, {"type": "error", "message": "Not ready."})
        return

    audio_b64 = data.get("data", "")
    if not audio_b64:
        return
    try:
        audio = base64.b64decode(audio_b64)
    except Exception as e:
        await manager.send(websocket, {"type": "error", "message": f"Bad voice audio: {e}"})
        return
    sample_rate = int(data.get("sample_rate", 16000))

    wake = ctx.kernel.get_service("wake_word")
    if wake is not None and not data.get("after_wake"):
        try:
            import array
            samples = array.array("h", audio[: len(audio) - len(audio) % 2])
            hit = await wake.process(samples)
            if not hit:
                await manager.send(websocket, {"type": "voice_status", "is_listening": True,
                                               "wake_detected": False})
                return
            await manager.send(websocket, {"type": "wake_detected", "is_listening": False})
        except Exception:
            pass

    stt = ctx.kernel.get_service("stt")
    try:
        text = await stt.transcribe(audio, sample_rate) if stt is not None else ""
    except Exception as e:
        print(f"[WS] STT error: {e}")
        text = ""
    await manager.send(websocket, {"type": "transcription", "text": text})
    if not text:
        return

    result = await process_text(app, text)
    tts = ctx.kernel.get_service("tts")
    audio_out = b""
    if tts is not None:
        try:
            audio_out = await tts.synthesize(result.get("narration", ""), ctx.personality.tts_params())
        except Exception as e:
            print(f"[WS] TTS error: {e}")
    await manager.send(websocket, {
        "type": "voice_response",
        "text": result.get("narration", ""),
        "intent": result.get("intent"),
        "audio_base64": base64.b64encode(audio_out).decode() if audio_out else "",
    })
