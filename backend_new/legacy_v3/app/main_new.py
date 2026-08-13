"""main_new.py - J.A.R.V.I.S. V3 FastAPI Application Entry Point.

New architecture (no Ollama dependency):
- AppKernel: plugin lifecycle management
- StateStore: centralized per-profile state
- VoicePipeline: composable flow (Listen->STT->LLM->TTS)
- CommandDispatcher: 3-step pipeline (regex->LLM JSON->chat)
- LLMService: direct GGUF inference
- Plugins: modular domain services (SmartHome, Browser, Vision, Monitoring, etc.)
- WebSocket: typed message contracts for Flutter client
"""

import asyncio
import os
import uvicorn
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.kernel import AppKernel
from app.state_store import StateStore
from app.llm_service import LLMService
from app.command_dispatcher import CommandDispatcher, register_handler

app = FastAPI(title="J.A.R.V.I.S. V3 - Local AI Assistant", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kernel: Optional[AppKernel] = None
state_store: Optional[StateStore] = None
llm_service: Optional[LLMService] = None
command_dispatcher: Optional[CommandDispatcher] = None


class WSConnectionManager:
    """Manage WebSocket connections for Flutter client."""

    def __init__(self):
        self.active_connections: set = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        disconnected = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        self.active_connections -= disconnected


manager = WSConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize J.A.R.V.I.S. V3 on startup."""
    global kernel, state_store, llm_service, command_dispatcher

    print("J.A.R.V.I.S. V3 starting up...")

    state_store = StateStore(db_path="jarvis_v3.db", data_dir="data")

    env_value = os.environ.get("JARVIS_SERVICES", "minimal")
    kernel = AppKernel(env_vars={"JARVIS_SERVICES": env_value})
    await kernel.startup(state_store)

    llm_service = LLMService()
    command_dispatcher = CommandDispatcher(llm_service=llm_service)

    plugin_map = {
        "voice_pipeline": ("app.plugins.voice_pipeline", "VoicePipelinePlugin"),
        "smart_home_plugin": ("app.plugins.smart_home", "SmartHomePlugin"),
        "monitoring_plugin": ("app.plugins.monitoring", "MonitoringPlugin"),
        "browser_automation": ("app.plugins.browser_automation", "BrowserAutomationPlugin"),
        "vision_plugin": ("app.plugins.vision", "VisionPlugin"),
        "wearable_service": ("app.plugins.wearable", "WearablePlugin"),
        "thermal_logger": ("app.plugins.thermal", "ThermalLoggerPlugin"),
        "mqtt_service": ("app.plugins.mqtt", "MQTTPlugin"),
    }

    for plugin_name, (module_path, class_name) in plugin_map.items():
        if kernel.is_plugin_enabled(plugin_name):
            try:
                module = __import__(module_path, fromlist=[class_name])
                plugin_cls = getattr(module, class_name)
                plugin = plugin_cls()
                await plugin.start(kernel)
                kernel.plugins[plugin_name] = plugin
            except Exception as e:
                print(f"Failed to start plugin {plugin_name}: {e}")

    await manager.broadcast({
        "type": "kernel_ready",
        "message": "J.A.R.V.I.S. V3 is ready",
        "enabled_plugins": kernel.active_plugins,
        "active_profile": state_store.get_active_profile() if state_store else "default"
    })

    print(f"J.A.R.V.I.S. V3 ready. Enabled plugins: {kernel.active_plugins}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of J.A.R.V.I.S. V3."""
    if kernel:
        print("J.A.R.V.I.S. V3 shutting down...")
        await kernel.shutdown()
    print("J.A.R.V.I.S. V3 shutdown complete")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Flutter client communication."""
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "voice_chunk":
                result = await handle_voice_chunk(data)
                await manager.send_personal_message(result, websocket)

            elif msg_type == "voice_command":
                text = data.get("text", "")
                result = await handle_text_command(text)
                await manager.send_personal_message(result, websocket)

            elif msg_type == "settings_update":
                profile = data.get("profile", "default")
                settings = data.get("settings", {})
                if state_store:
                    for key, value in settings.items():
                        state_store.set(profile, f"settings.{key}", value)
                await manager.send_personal_message({
                    "type": "settings_updated",
                    "profile": profile,
                    "success": True
                }, websocket)

            elif msg_type == "plugin_control":
                plugin_name = data.get("name")
                enabled = data.get("enabled", False)
                if kernel:
                    was_enabled = kernel.is_plugin_enabled(plugin_name)
                    if enabled and not was_enabled:
                        await kernel._start_plugin(plugin_name)
                    elif not enabled and was_enabled:
                        await kernel._stop_plugin(plugin_name)
                await manager.send_personal_message({
                    "type": "plugin_status",
                    "name": plugin_name,
                    "enabled": kernel.is_plugin_enabled(plugin_name) if kernel else False
                }, websocket)

            elif msg_type == "knowledge_search":
                query = data.get("query", "")
                await manager.send_personal_message({
                    "type": "knowledge_results",
                    "query": query,
                    "results": [],
                    "success": True
                }, websocket)

            elif msg_type == "switch_profile":
                new_profile = data.get("profile", "default")
                if state_store:
                    state_store.switch_profile(new_profile)
                await manager.send_personal_message({
                    "type": "profile_switched",
                    "profile": new_profile,
                    "success": True
                }, websocket)

            else:
                await manager.send_personal_message({
                    "type": "error",
                    "code": "unknown_message",
                    "message": f"Unknown message type: {msg_type}"
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket client disconnected")


async def handle_voice_chunk(data: dict) -> dict:
    """Handle a voice chunk message through the voice pipeline."""
    await asyncio.sleep(0.01)
    return {
        "type": "voice_status",
        "is_listening": True,
        "wake_detected": False,
        "simulated": True
    }


async def handle_text_command(text: str) -> dict:
    """Handle a text command, dispatching through the command pipeline."""
    if not command_dispatcher:
        return {
            "type": "command_result",
            "success": False,
            "result_text": "Command dispatcher not initialized.",
            "handler": None
        }

    result = await command_dispatcher.dispatch(text)

    ws_message = {
        "type": "command_result",
        "success": result.get("success", False),
        "result_text": result.get("narration", "Command processed."),
        "handler": result.get("handler"),
        "command_type": result.get("command_type"),
    }

    if result.get("params"):
        ws_message["params"] = result["params"]

    return ws_message


async def handle_system_shutdown(params: dict) -> dict:
    return {"success": True, "narration": "Shutting down the system.", "type": "system_action"}


async def handle_system_restart(params: dict) -> dict:
    return {"success": True, "narration": "Restarting the system.", "type": "system_action"}


async def handle_smart_home_turn_on(params: dict) -> dict:
    device = params.get("device", "lights")
    return {"success": True, "narration": f"Turning on the {device}.", "type": "smart_home_action"}


async def handle_smart_home_turn_off(params: dict) -> dict:
    device = params.get("device", "lights")
    return {"success": True, "narration": f"Turning off the {device}.", "type": "smart_home_action"}


async def handle_info_time(params: dict) -> dict:
    import datetime
    now = datetime.datetime.now()
    return {"success": True, "narration": f"The current time is {now.strftime('%H:%M')}.", "type": "info_response"}


async def handle_media_play(params: dict) -> dict:
    return {"success": True, "narration": "Playing media.", "type": "media_action"}


async def handle_voice_chat(params: dict) -> dict:
    return {"success": True, "narration": "I'm here. How can I help you today?", "type": "conversational"}


register_handler("system_shutdown", handle_system_shutdown)
register_handler("system_restart", handle_system_restart)
register_handler("smart_home_turn_on", handle_smart_home_turn_on)
register_handler("smart_home_turn_off", handle_smart_home_turn_off)
register_handler("info_time", handle_info_time)
register_handler("media_play", handle_media_play)
register_handler("voice_chat", handle_voice_chat)


@app.get("/")
async def root():
    return {
        "name": "J.A.R.V.I.S. V3",
        "version": "3.0.0",
        "status": "operational",
        "description": "Local AI Assistant - No Ollama dependency"
    }


@app.get("/health")
async def health():
    llm_loaded = llm_service.is_loaded() if llm_service else False
    return {
        "status": "healthy" if llm_loaded else "degraded",
        "llm_loaded": llm_loaded,
        "plugins": kernel.active_plugins if kernel else [],
        "active_profile": state_store.get_active_profile() if state_store else "default"
    }


@app.get("/plugins")
async def list_plugins():
    if kernel:
        return {"enabled": kernel.active_plugins, "all_registered": list(kernel.plugins.keys())}
    return {"enabled": [], "all_registered": []}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)