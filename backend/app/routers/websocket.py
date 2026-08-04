from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
import asyncio
from datetime import datetime, timezone
from app.services.voice_service import voice_service
from app.services.screen_share_service import screen_share_service
from app.services.rtsp_service import rtsp_service
from app.services.wearable_service import wearable_service
from app.services.command_registry import command_registry
from app.services.vision_service import vision_service
from app.services.system_command_service import system_command_service
from app.services.hermes_browser import hermes_browser
from app.services.personality_service import personality_service
from app.services.voice_session_service import VoiceSession

router = APIRouter()

from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class ClientInfo:
    ws: WebSocket
    client_id: int
    device_id: str = ""
    profile_id: str = ""


connected_clients: dict[str, list[ClientInfo]] = defaultdict(list)


def _build_system_prompt(extra_instructions: str = "", user_message: str = "", profile_id: str = "default") -> str:
    """Build system prompt with browser state and RAG context."""
    base_prompt = personality_service.get_system_prompt(profile_id)
    browser_state = hermes_browser.get_browser_state_for_llm()
    
    prompt = f"You are JARVIS.\n{base_prompt}"
    
    if browser_state and "No active" not in browser_state:
        prompt += f"\n\nCurrent browser state:\n{browser_state}"
    
    if user_message:
        try:
            from app.services.rag_service import rag_service
            rag_context = rag_service.get_context_for_llm(user_message, top_k=3)
            if rag_context:
                prompt += f"\n\n{rag_context}"
        except Exception:
            pass
    
    if extra_instructions:
        prompt += f"\n{extra_instructions}"
    
    return prompt


def _register_system_handlers():
    from urllib.parse import quote
    scs = system_command_service
    command_registry.register_handler("open_app", scs.open_app)
    command_registry.register_handler("open_browser", scs.open_browser)

    async def browser_open_youtube(query: str = "") -> dict:
        print(f"[YOUTUBE] Opening YouTube with query: '{query}'")
        if not await _ensure_browser_session():
            print("[YOUTUBE] Browser session not available")
            return {"status": "error", "message": "Could not start browser"}
        query = query.strip()
        if query:
            url = f"https://www.youtube.com/results?search_query={quote(query)}"
        else:
            url = "https://www.youtube.com"
        result = await hermes_browser.navigate("default", url)
        if result["status"] == "success" and query:
            video_result = await hermes_browser.click_first_youtube_video("default")
            if video_result["status"] == "success":
                result["message"] = f"Playing {query} on YouTube"
                result["playing"] = True
        print(f"[YOUTUBE] Result: {result}")
        return result

    async def browser_play_youtube(query: str = "") -> dict:
        print(f"[YOUTUBE] Playing on YouTube with query: '{query}'")
        if not await _ensure_browser_session():
            print("[YOUTUBE] Browser session not available")
            return {"status": "error", "message": "Could not start browser"}
        query = query.strip()
        if query:
            url = f"https://www.youtube.com/results?search_query={quote(query)}"
        else:
            url = "https://music.youtube.com"
        result = await hermes_browser.navigate("default", url)
        if result["status"] == "success" and query:
            video_result = await hermes_browser.click_first_youtube_video("default")
            if video_result["status"] == "success":
                result["message"] = f"Playing {query} on YouTube Music"
                result["playing"] = True
        print(f"[YOUTUBE] Result: {result}")
        return result

    command_registry.register_handler("open_youtube", browser_open_youtube)
    command_registry.register_handler("play_youtube", browser_play_youtube)
    command_registry.register_handler("open_file_explorer", scs.open_file_explorer)
    command_registry.register_handler("open_terminal", scs.open_terminal)
    command_registry.register_handler("open_opencode", scs.open_opencode)
    command_registry.register_handler("close_app", scs.close_app)
    command_registry.register_handler("screenshot", scs.screenshot)
    command_registry.register_handler("list_processes", scs.list_processes)
    command_registry.register_handler("get_system_info", scs.get_system_info)
    command_registry.register_handler("get_disk_usage", scs.get_disk_usage)
    command_registry.register_handler("set_volume", scs.set_volume)
    command_registry.register_handler("mute", scs.mute)
    command_registry.register_handler("next_track", scs.next_track)
    command_registry.register_handler("previous_track", scs.previous_track)
    command_registry.register_handler("play_pause", scs.play_pause)
    command_registry.register_handler("shutdown", scs.shutdown)
    command_registry.register_handler("restart", scs.restart)
    command_registry.register_handler("lock_pc", scs.lock_pc)
    command_registry.register_handler("sleep_pc", scs.sleep_pc)
    command_registry.register_handler("run_command", scs.run_command)
    command_registry.register_handler("search_files", scs.search_files)
    command_registry.register_handler("list_dir", scs.list_dir)
    command_registry.register_handler("navigate_to", scs.navigate_to)
    command_registry.register_handler("go_back", scs.go_back)
    command_registry.register_handler("go_home", scs.go_home)
    command_registry.register_handler("open_file", scs.open_file)
    command_registry.register_handler("read_file", scs.read_file)
    command_registry.register_handler("get_current_location", scs.get_current_location)
    command_registry.register_handler("get_folder_map", scs.get_folder_map)
    command_registry.register_handler("deep_scan", scs.deep_scan)
    command_registry.register_handler("remember", scs.remember)
    command_registry.register_handler("recall", scs.recall)
    command_registry.register_handler("forget", scs.forget)
    command_registry.register_handler("get_time", scs.get_time)
    command_registry.register_handler("get_date", scs.get_date)

    from app.services.monitoring_service import monitoring_service
    from app.services.alert_engine import alert_engine
    from app.services.activity_logger import activity_logger

    async def system_health_handler() -> dict:
        return await asyncio.to_thread(monitoring_service.get_snapshot)

    async def get_alerts_handler() -> dict:
        alerts = await asyncio.to_thread(alert_engine.get_alert_history)
        return {"status": "success", "alerts": alerts}

    async def get_activity_log_handler() -> dict:
        activity = await asyncio.to_thread(activity_logger.get_recent_activity)
        return {"status": "success", "activity": activity}

    async def get_active_window_handler() -> dict:
        history = await asyncio.to_thread(activity_logger.get_active_window_history, 60)
        return {"status": "success", "windows": history}

    async def get_top_processes_handler() -> dict:
        processes = await asyncio.to_thread(activity_logger.get_top_processes)
        return {"status": "success", "processes": processes}

    async def set_alert_threshold_handler(metric: str = "", value: float = 0) -> dict:
        if not metric:
            return {"status": "error", "message": "metric required"}
        monitoring_service.set_threshold(metric, value)
        return {"status": "success", "message": f"Set {metric} threshold to {value}"}

    async def get_alert_thresholds_handler() -> dict:
        return {"status": "success", "thresholds": monitoring_service.get_thresholds()}

    command_registry.register_handler("system_health", system_health_handler)
    command_registry.register_handler("get_alerts", get_alerts_handler)
    command_registry.register_handler("get_activity_log", get_activity_log_handler)
    command_registry.register_handler("get_active_window", get_active_window_handler)
    command_registry.register_handler("get_top_processes", get_top_processes_handler)
    command_registry.register_handler("set_alert_threshold", set_alert_threshold_handler)
    command_registry.register_handler("get_alert_thresholds", get_alert_thresholds_handler)

    from app.services.briefing_service import briefing_service

    async def morning_briefing_handler() -> dict:
        result = await briefing_service.generate_briefing(include_tts=False)
        return {"status": "success", "briefing": result}

    async def briefing_config_handler(source: str = "", enabled: str = "") -> dict:
        if source and enabled:
            briefing_service.configure({source: enabled.lower() in ("true", "1", "on")})
        return {"status": "success", "config": briefing_service.get_config()}

    command_registry.register_handler("morning_briefing", morning_briefing_handler)
    command_registry.register_handler("briefing_config", briefing_config_handler)

    from app.services.routine_service import routine_service

    async def create_routine_handler(name: str = "", description: str = "", steps: str = "") -> dict:
        import json as _json
        try:
            step_list = _json.loads(steps) if steps else []
        except _json.JSONDecodeError:
            return {"status": "error", "message": "Invalid steps JSON"}
        return routine_service.create(name, description, step_list)

    async def run_routine_handler(name: str = "") -> dict:
        if not name:
            return {"status": "error", "message": "Routine name required"}
        return await routine_service.run(name)

    async def list_routines_handler() -> dict:
        return {"status": "success", "routines": routine_service.get_all()}

    async def delete_routine_handler(name: str = "") -> dict:
        if not name:
            return {"status": "error", "message": "Routine name required"}
        return routine_service.delete(name)

    command_registry.register_handler("create_routine", create_routine_handler)
    command_registry.register_handler("run_routine", run_routine_handler)
    command_registry.register_handler("list_routines", list_routines_handler)
    command_registry.register_handler("delete_routine", delete_routine_handler)

    from app.services.email_service import email_service
    from app.services.screen_context_service import screen_context_service
    from app.services.notification_service import notification_service

    async def check_email_handler() -> dict:
        emails = await email_service.get_recent(limit=5)
        return {"status": "success", "emails": emails}

    async def email_summary_handler() -> dict:
        summary = await email_service.get_summary(limit=5)
        return {"status": "success", "summary": summary}

    async def screen_context_handler() -> dict:
        result = await screen_context_service.capture_and_summarize()
        return result

    async def get_notifications_handler() -> dict:
        return {"status": "success", "notifications": notification_service.get_recent()}

    command_registry.register_handler("check_email", check_email_handler)
    command_registry.register_handler("email_summary", email_summary_handler)
    command_registry.register_handler("screen_context", screen_context_handler)
    command_registry.register_handler("get_notifications", get_notifications_handler)

    from app.services.suggestion_engine import suggestion_engine

    async def get_suggestions_handler() -> dict:
        from app.services.monitoring_service import monitoring_service
        monitoring_data = monitoring_service.get_snapshot()
        suggestions = await suggestion_engine.evaluate(monitoring_data=monitoring_data)
        return {"status": "success", "suggestions": suggestions}

    async def dismiss_suggestion_handler(suggestion_id: str = "") -> dict:
        if not suggestion_id:
            return {"status": "error", "message": "suggestion_id required"}
        suggestion_engine.dismiss(suggestion_id)
        return {"status": "success", "message": "Dismissed"}

    command_registry.register_handler("get_suggestions", get_suggestions_handler)
    command_registry.register_handler("dismiss_suggestion", dismiss_suggestion_handler)

    from app.services.personality_enhancer import personality_enhancer

    async def personality_enhance_handler(text: str = "", context: str = "") -> dict:
        enhanced = personality_enhancer.enhance_response(text, context)
        return {"status": "success", "enhanced": enhanced, "original": text}

    async def personality_config_handler(setting: str = "", value: str = "") -> dict:
        if setting and value:
            if setting == "formality":
                personality_enhancer.set_formality(float(value))
            elif setting == "quip_frequency":
                personality_enhancer.set_quip_frequency(float(value))
            elif setting == "enabled":
                personality_enhancer.set_enabled(value.lower() in ("true", "1", "on"))
        return {"status": "success", "config": personality_enhancer.get_config()}

    command_registry.register_handler("personality_enhance", personality_enhance_handler)
    command_registry.register_handler("personality_config", personality_config_handler)

    from app.services.device_mesh_service import device_mesh_service

    async def send_to_device_handler(device_id: str = "", content: str = "") -> dict:
        if not device_id or not content:
            return {"status": "error", "message": "device_id and content required"}
        device_mesh_service.queue_message(device_id, {"type": "push_message", "content": content})
        return {"status": "success", "message": f"Queued for {device_id}"}

    async def sync_clipboard_handler() -> dict:
        clip = device_mesh_service.get_clipboard()
        if clip:
            return {"status": "success", "clipboard": clip}
        return {"status": "success", "clipboard": None}

    async def transfer_file_handler(file_path: str = "", target_device: str = "") -> dict:
        if not file_path or not target_device:
            return {"status": "error", "message": "file_path and target_device required"}
        return await device_mesh_service.prepare_file_transfer(file_path, target_device)

    command_registry.register_handler("send_to_device", send_to_device_handler)
    command_registry.register_handler("sync_clipboard", sync_clipboard_handler)
    command_registry.register_handler("transfer_file", transfer_file_handler)

    from app.services.knowledge_service import knowledge_service
    command_registry.register_handler("knowledge_summary", lambda: knowledge_service.get_stats())
    command_registry.register_handler("knowledge_search", knowledge_service.search)

    from app.services.rag_service import rag_service
    from app.services.ocr_service import ocr_service

    async def rag_ingest_handler(text_or_file: str = "") -> dict:
        text_or_file = text_or_file.strip()
        if not text_or_file:
            return {"status": "error", "message": "Provide text to learn or a file path"}
        path = Path(text_or_file)
        if path.exists() and path.is_file():
            return await asyncio.to_thread(rag_service.ingest_file, str(path))
        count = await asyncio.to_thread(rag_service.ingest_text, text_or_file, "voice_input")
        return {"status": "success", "chunks_added": count, "message": f"Learned from text ({count} chunks)"}

    async def rag_search_handler(query: str = "") -> dict:
        if not query.strip():
            return {"status": "error", "message": "Provide a search query"}
        results = await asyncio.to_thread(rag_service.search, query.strip(), 5, 0.3)
        if not results:
            return {"status": "success", "results": [], "message": "No relevant knowledge found"}
        return {"status": "success", "results": results, "message": f"Found {len(results)} relevant results"}

    async def rag_status_handler() -> dict:
        return await asyncio.to_thread(rag_service.get_stats)

    async def rag_clear_handler() -> dict:
        count = await asyncio.to_thread(rag_service.clear_all)
        return {"status": "success", "cleared": count, "message": f"Cleared {count} chunks from knowledge base"}

    async def ocr_screenshot_handler(prompt: str = "") -> dict:
        return await ocr_service.ocr_screenshot(prompt=prompt if prompt else None)

    async def ocr_file_handler(file_path: str = "") -> dict:
        file_path = file_path.strip()
        if not file_path:
            return {"status": "error", "message": "Provide a file path"}
        return await ocr_service.ocr_from_file(file_path)

    command_registry.register_handler("rag_ingest", rag_ingest_handler)
    command_registry.register_handler("rag_search", rag_search_handler)
    command_registry.register_handler("rag_status", rag_status_handler)
    command_registry.register_handler("rag_clear", rag_clear_handler)
    command_registry.register_handler("ocr_screenshot", ocr_screenshot_handler)
    command_registry.register_handler("ocr_file", ocr_file_handler)

    async def _ensure_browser_session() -> bool:
        session = hermes_browser.get_session("default")
        if session:
            return True
        
        # Try to create session with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await hermes_browser.create_session("default")
                return True
            except Exception as e:
                print(f"[BROWSER] Session creation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        return False

    async def browser_search_handler(query: str) -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.search_google("default", query)

    async def browser_navigate_handler(url: str) -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.navigate("default", url)

    async def browser_click_handler(ref: str) -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.click("default", ref)

    async def browser_type_handler(text: str, ref: str = "input") -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.type_text("default", ref, text)

    async def browser_screenshot_handler() -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.screenshot("default")

    async def browser_scroll_handler(direction: str = "down") -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.scroll("default", direction)

    async def browser_snapshot_handler() -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.get_snapshot("default")

    async def browser_back_handler() -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.go_back("default")

    async def browser_forward_handler() -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.go_forward("default")

    async def browser_start_handler() -> dict:
        session = await hermes_browser.create_session("default")
        return {"status": "success", "session_id": session.session_id, "message": "Browser started"}

    async def browser_stop_handler() -> dict:
        await hermes_browser.destroy_session("default")
        return {"status": "success", "message": "Browser stopped"}

    async def browser_new_tab_handler() -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.new_tab("default")

    async def browser_switch_tab_handler(tab_index: int = 0) -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.switch_tab("default", tab_index)

    async def browser_close_tab_handler(tab_index: str = "") -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        idx = int(tab_index) if tab_index and tab_index.isdigit() else None
        return await hermes_browser.close_tab("default", idx)

    async def browser_get_tabs_handler() -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.get_all_tabs_info("default")

    async def browser_page_summary_handler() -> dict:
        if not await _ensure_browser_session():
            return {"status": "error", "message": "Could not start browser"}
        return await hermes_browser.get_page_summary("default")

    command_registry.register_handler("browser_search", browser_search_handler)
    command_registry.register_handler("browser_navigate", browser_navigate_handler)
    command_registry.register_handler("browser_click", browser_click_handler)
    command_registry.register_handler("browser_type", browser_type_handler)
    command_registry.register_handler("browser_screenshot", browser_screenshot_handler)
    command_registry.register_handler("browser_scroll", browser_scroll_handler)
    command_registry.register_handler("browser_snapshot", browser_snapshot_handler)
    command_registry.register_handler("browser_back", browser_back_handler)
    command_registry.register_handler("browser_forward", browser_forward_handler)
    command_registry.register_handler("browser_start", browser_start_handler)
    command_registry.register_handler("browser_stop", browser_stop_handler)
    command_registry.register_handler("browser_new_tab", browser_new_tab_handler)
    command_registry.register_handler("browser_switch_tab", browser_switch_tab_handler)
    command_registry.register_handler("browser_close_tab", browser_close_tab_handler)
    command_registry.register_handler("browser_get_tabs", browser_get_tabs_handler)
    command_registry.register_handler("browser_page_summary", browser_page_summary_handler)


_register_system_handlers()
client_devices: dict[int, str] = {}
client_viewer_sessions: dict[int, str] = {}
client_camera_viewers: dict[int, str] = {}
introduction_pending: set[int] = set()

_heartbeat_task = None

COMMAND_RESPONSES = {
    "open_youtube": "Opening YouTube for you.",
    "play_youtube": "Playing that on YouTube now.",
    "open_browser": "Opening your browser.",
    "open_app": "Opening that app for you.",
    "close_app": "Closing that app.",
    "screenshot": "Taking a screenshot.",
    "set_volume": "Adjusting the volume.",
    "mute": "Muted.",
    "unmute": "Unmuted.",
    "next_track": "Skipping to the next track.",
    "previous_track": "Going back to the previous track.",
    "play_pause": "Toggling playback.",
    "shutdown": "Shutting down.",
    "restart": "Restarting your PC.",
    "lock_pc": "Locking your screen.",
    "sleep_pc": "Putting your PC to sleep.",
    "open_file_explorer": "Opening File Explorer.",
    "open_terminal": "Opening terminal.",
    "navigate_to": "Navigating there.",
    "go_back": "Going back.",
    "go_home": "Going home.",
    "list_dir": "Here are your files.",
    "search_files": "Searching for files.",
    "browser_search": "Searching the web.",
    "browser_navigate": "Navigating there.",
    "browser_click": "Clicking that.",
    "browser_type": "Typing that in.",
    "browser_scroll": "Scrolling.",
    "browser_screenshot": "Taking a screenshot.",
    "browser_snapshot": "Getting page content.",
    "browser_back": "Going back.",
    "browser_forward": "Going forward.",
    "browser_new_tab": "Opening a new tab.",
    "browser_switch_tab": "Switching tabs.",
    "browser_close_tab": "Closing that tab.",
    "browser_get_tabs": "Here are your open tabs.",
    "browser_page_summary": "Let me describe the page.",
    "rag_ingest": "Learning from that.",
    "rag_search": "Searching my knowledge.",
    "rag_status": "Here's my knowledge status.",
    "rag_clear": "Knowledge cleared.",
    "ocr_screenshot": "Reading the screen.",
    "ocr_file": "Reading that image.",
    "remember": "I'll remember that.",
    "recall": "Let me check my memory.",
    "forget": "Done, I've forgotten that.",
    "get_time": None,
    "get_date": None,
    "list_processes": None,
    "get_system_info": None,
    "get_disk_usage": None,
    "system_health": "Checking system health.",
    "get_alerts": "Retrieving alerts.",
    "get_activity_log": "Pulling activity log.",
    "get_active_window": "Checking active window.",
    "get_top_processes": "Listing top processes.",
    "set_alert_threshold": "Updating alert threshold.",
    "get_alert_thresholds": "Here are the thresholds.",
    "morning_briefing": "Assembling your briefing.",
    "briefing_config": "Updating briefing config.",
    "wake_word_start": "Listening for wake word.",
    "wake_word_stop": "Wake word detection stopped.",
    "wake_word_config": "Updating wake word config.",
    "run_routine": "Running routine.",
    "create_routine": "Creating routine.",
    "list_routines": "Here are your routines.",
    "delete_routine": "Routine deleted.",
    "check_email": "Checking your email.",
    "email_summary": "Summarizing your emails.",
    "screen_context": "Reading the screen.",
    "get_notifications": "Here are your notifications.",
    "get_suggestions": "Let me think of some suggestions.",
    "dismiss_suggestion": "Suggestion dismissed.",
    "personality_enhance": "Enhancing that response.",
    "personality_config": "Updating personality settings.",
    "send_to_device": "Sending to device.",
    "sync_clipboard": "Syncing clipboard.",
    "transfer_file": "Preparing file transfer.",
}


async def _heartbeat_loop():
    while True:
        await asyncio.sleep(15)
        for profile_id in list(connected_clients.keys()):
            remaining = []
            for info in connected_clients[profile_id]:
                try:
                    await info.ws.send_json({"type": "ping"})
                    remaining.append(info)
                except Exception:
                    pass
            if remaining:
                connected_clients[profile_id] = remaining
            else:
                del connected_clients[profile_id]


async def safe_send(ws: WebSocket, message: dict) -> bool:
    try:
        await ws.send_json(message)
        return True
    except Exception:
        return False


async def broadcast(message: dict, exclude: WebSocket = None, profile_id: str = None):
    for pid in list(connected_clients.keys()):
        if profile_id and pid != profile_id:
            continue
        for info in connected_clients[pid]:
            if info.ws != exclude:
                try:
                    await info.ws.send_json(message)
                except:
                    pass


async def send_to_device(device_id: str, message: dict):
    for info_list in connected_clients.values():
        for info in info_list:
            if info.device_id == device_id:
                try:
                    await info.ws.send_json(message)
                except:
                    pass


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    from app.services.auth_service import auth_service
    profile_id = auth_service.resolve_token(token) if token else None
    await websocket.accept()
    client_id = id(websocket)

    ci = ClientInfo(ws=websocket, client_id=client_id, profile_id=profile_id or "default")
    connected_clients[ci.profile_id].append(ci)

    global _heartbeat_task
    if _heartbeat_task is None or _heartbeat_task.done():
        _heartbeat_task = asyncio.create_task(_heartbeat_loop())

    greeted_clients = getattr(websocket_endpoint, '_greeted', set())
    try:
        await broadcast({
            "type": "client_connected",
            "client_id": client_id,
        }, websocket)

        if client_id not in greeted_clients:
            greeted_clients.add(client_id)
            websocket_endpoint._greeted = greeted_clients
            await send_greeting(websocket, ci.profile_id)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "text_message":
                asyncio.create_task(handle_text_message(websocket, message, ci.profile_id))
            elif msg_type == "ping":
                await safe_send(websocket,{"type": "pong"})
            elif msg_type == "device_register":
                await handle_device_register(websocket, message, client_id, ci.profile_id)
            elif msg_type == "device_heartbeat":
                await handle_device_heartbeat(websocket, message)
            elif msg_type == "device_status_update":
                await handle_device_status_update(websocket, message)
            elif msg_type == "screen_frame":
                await handle_screen_frame(websocket, message)
            elif msg_type == "screen_start":
                await handle_screen_start(websocket, message)
            elif msg_type == "screen_stop":
                await handle_screen_stop(websocket, message)
            elif msg_type == "screen_view":
                await handle_screen_view(websocket, message, client_id)
            elif msg_type == "screen_unview":
                await handle_screen_unview(websocket, message, client_id)
            elif msg_type == "screen_analyze":
                await handle_screen_analyze(websocket, message, ci.profile_id)
            elif msg_type == "camera_view":
                await handle_camera_view(websocket, message, client_id)
            elif msg_type == "camera_unview":
                await handle_camera_unview(websocket, message, client_id)
            elif msg_type == "camera_frame_request":
                await handle_camera_frame_request(websocket, message)
            elif msg_type == "wearable_subscribe":
                await handle_wearable_subscribe(websocket, message, client_id)
            elif msg_type == "wearable_unsubscribe":
                await handle_wearable_unsubscribe(websocket, message, client_id)
            elif msg_type == "wearable_health_update":
                await handle_wearable_health_update(websocket, message)
            elif msg_type == "vision_analyze":
                await handle_vision_analyze(websocket, message)
            elif msg_type == "vision_quick_look":
                await handle_vision_quick_look(websocket, message)
            elif msg_type == "vision_scan_all":
                await handle_vision_scan_all(websocket)
            elif msg_type == "vision_observe_start":
                await handle_vision_observe_start(websocket, message)
            elif msg_type == "vision_observe_stop":
                await handle_vision_observe_stop(websocket, message)
            elif msg_type == "voice_profile_switch":
                await handle_voice_profile_switch(websocket, message)
            elif msg_type == "personality_update":
                await handle_personality_update(websocket, message, ci.profile_id)
            elif msg_type == "browser_create_session":
                await handle_browser_create_session(websocket, message)
            elif msg_type == "browser_destroy_session":
                await handle_browser_destroy_session(websocket, message)
            elif msg_type == "browser_navigate":
                await handle_browser_navigate(websocket, message)
            elif msg_type == "browser_click":
                await handle_browser_click(websocket, message)
            elif msg_type == "browser_type":
                await handle_browser_type(websocket, message)
            elif msg_type == "browser_screenshot":
                await handle_browser_screenshot(websocket, message)
            elif msg_type == "browser_snapshot":
                await handle_browser_snapshot(websocket, message)
            elif msg_type == "browser_scroll":
                await handle_browser_scroll(websocket, message)
            elif msg_type == "browser_search":
                await handle_browser_search(websocket, message)
            elif msg_type == "browser_get_state":
                await handle_browser_get_state(websocket, message)
            elif msg_type == "browser_new_tab":
                await handle_browser_new_tab(websocket, message)
            elif msg_type == "browser_switch_tab":
                await handle_browser_switch_tab(websocket, message)
            elif msg_type == "browser_close_tab":
                await handle_browser_close_tab(websocket, message)
            elif msg_type == "browser_page_summary":
                await handle_browser_page_summary(websocket, message)
            elif msg_type == "rag_ingest":
                await handle_rag_ingest(websocket, message)
            elif msg_type == "rag_search":
                await handle_rag_search(websocket, message)
            elif msg_type == "rag_status":
                await handle_rag_status(websocket)
            elif msg_type == "ocr_image":
                await handle_ocr_image(websocket, message)
            elif msg_type == "ocr_screenshot":
                await handle_ocr_screenshot(websocket, message)
            elif msg_type == "farewell":
                await handle_farewell(websocket, ci.profile_id)
            elif msg_type == "greeting":
                await send_greeting(websocket, ci.profile_id)
            elif msg_type == "monitoring_snapshot":
                await handle_monitoring_snapshot(websocket)
            elif msg_type == "monitoring_history":
                await handle_monitoring_history(websocket, message)
            elif msg_type == "monitoring_alerts":
                await handle_monitoring_alerts(websocket, message)
            elif msg_type == "monitoring_thresholds":
                await handle_monitoring_thresholds(websocket)
            elif msg_type == "monitoring_set_threshold":
                await handle_monitoring_set_threshold(websocket, message)
            elif msg_type == "activity_log":
                await handle_activity_log(websocket, message)
            elif msg_type == "activity_window":
                await handle_activity_window(websocket, message)
            elif msg_type == "activity_processes":
                await handle_activity_processes(websocket)
            elif msg_type == "morning_briefing":
                await handle_morning_briefing(websocket, message)
            elif msg_type == "briefing_config":
                await handle_briefing_config(websocket, message)
            elif msg_type == "wake_word_config":
                await handle_wake_word_config(websocket, message)
            elif msg_type == "run_routine":
                await handle_run_routine(websocket, message)
            elif msg_type == "create_routine":
                await handle_create_routine(websocket, message)
            elif msg_type == "list_routines":
                await handle_list_routines(websocket)
            elif msg_type == "delete_routine":
                await handle_delete_routine(websocket, message)
            elif msg_type == "check_email":
                await handle_check_email(websocket, message)
            elif msg_type == "email_summary":
                await handle_email_summary(websocket, message)
            elif msg_type == "screen_context":
                await handle_screen_context(websocket, message)
            elif msg_type == "get_notifications":
                await handle_get_notifications(websocket, message)
            elif msg_type == "get_suggestions":
                await handle_get_suggestions(websocket)
            elif msg_type == "dismiss_suggestion":
                await handle_dismiss_suggestion(websocket, message)
            elif msg_type == "personality_enhance":
                await handle_personality_enhance(websocket, message)
            elif msg_type == "personality_config":
                await handle_personality_config(websocket, message)
            elif msg_type == "mesh_register":
                await handle_device_mesh_register(websocket, message)
            elif msg_type == "mesh_heartbeat":
                await handle_device_mesh_heartbeat(websocket, message)
            elif msg_type == "push_to_device":
                await handle_push_to_device(websocket, message)
            elif msg_type == "clipboard_sync":
                await handle_sync_clipboard(websocket, message)
            elif msg_type == "transfer_file":
                await handle_transfer_file(websocket, message)
            elif msg_type == "transfer_chunk":
                await handle_transfer_chunk(websocket, message)
            elif msg_type == "mesh_devices":
                await handle_device_mesh_devices(websocket)
            elif msg_type == "voice_mode_start":
                await handle_voice_mode_start(websocket, ci.profile_id)
            elif msg_type == "audio_frame":
                await handle_audio_frame(websocket, message)
            elif msg_type == "tts_done":
                await handle_tts_done(websocket)
            elif msg_type == "voice_mode_stop":
                await handle_voice_mode_stop(websocket)
            else:
                await broadcast(message, websocket)

    except WebSocketDisconnect:
        introduction_pending.discard(client_id)
        session = voice_sessions.pop(client_id, None)
        if session is not None:
            await session.stop()
        info_list = connected_clients.get(ci.profile_id, [])
        connected_clients[ci.profile_id] = [c for c in info_list if c.client_id != client_id]
        if not connected_clients[ci.profile_id]:
            del connected_clients[ci.profile_id]

        device_id = client_devices.pop(client_id, None)

        session_id = client_viewer_sessions.pop(client_id, None)
        if session_id:
            screen_share_service.remove_viewer(session_id, str(client_id))

        camera_id = client_camera_viewers.pop(client_id, None)
        if camera_id:
            rtsp_service.remove_viewer(camera_id, str(client_id))

        wearable_service.unsubscribe(str(client_id))

        await broadcast({
            "type": "device_disconnected",
            "client_id": client_id,
            "device_id": device_id,
        })


async def send_greeting(websocket: WebSocket, profile_id: str = "default"):
    from app.services.voice_service import voice_service
    from app.services.voice_profile_service import voice_profile_service

    try:
        pdata = personality_service.get_profile(profile_id)
        if not pdata.introduced:
            introduction_pending.add(id(websocket))
            intro_text = (
                f"Hello! I am JARVIS, your personal AI assistant. "
                f"I am here to help you with anything you need. "
                f"But first, what should I call you?"
            )

            profile = voice_profile_service.get_active_profile()
            tts_audio = await voice_service.text_to_speech(
                intro_text,
                voice=profile.voice,
                rate=profile.rate,
                pitch=profile.pitch,
            )

            await safe_send(websocket,{
                "type": "avatar_state",
                "state": "speaking"
            })

            await safe_send(websocket,{
                "type": "voice_response",
                "response": intro_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "introduction",
                "is_introduction": True,
            })

            await safe_send(websocket,{
                "type": "avatar_state",
                "state": "idle"
            })
            return

        hour = datetime.now().hour

        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        else:
            period = "evening"

        greeting_text = f"Good {period}, {pdata.preferred_name}. How may I assist you today?"

        profile = voice_profile_service.get_active_profile()
        tts_audio = await voice_service.text_to_speech(
            greeting_text,
            voice=profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        await safe_send(websocket,{
            "type": "avatar_state",
            "state": "speaking"
        })

        await safe_send(websocket,{
            "type": "voice_response",
            "response": greeting_text,
            "audio": base64.b64encode(tts_audio).decode(),
            "model": "greeting",
            "is_greeting": True,
        })

        from app.services.settings_service import settings_service
        from app.services.tailscale_service import tailscale_service

        await safe_send(websocket,{
            "type": "welcome_info",
            "settings": settings_service.get_all(),
            "tailscale": await tailscale_service.get_status(),
        })

        await safe_send(websocket,{
            "type": "avatar_state",
            "state": "idle"
        })
    except Exception as e:
        print(f"[GREETING ERROR] {e}")


async def handle_farewell(websocket: WebSocket, profile_id: str = "default"):
    from app.services.voice_service import voice_service
    from app.services.voice_profile_service import voice_profile_service

    pdata = personality_service.get_profile(profile_id)
    try:
        hour = datetime.now().hour

        if 5 <= hour < 12:
            farewell_text = f"Good morning, {pdata.preferred_name}. Have a productive day ahead."
        elif 12 <= hour < 17:
            farewell_text = f"Good afternoon, {pdata.preferred_name}. I will be here when you need me."
        elif 17 <= hour < 21:
            farewell_text = f"Good evening, {pdata.preferred_name}. Take care and I will see you later."
        else:
            farewell_text = f"Good night, {pdata.preferred_name}. Sleep well and I will be ready when you return."

        profile = voice_profile_service.get_active_profile()
        tts_audio = await voice_service.text_to_speech(
            farewell_text,
            voice=profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        await safe_send(websocket,{
            "type": "avatar_state",
            "state": "speaking"
        })

        await safe_send(websocket,{
            "type": "voice_response",
            "response": farewell_text,
            "audio": base64.b64encode(tts_audio).decode(),
            "model": "farewell",
            "is_farewell": True,
        })

        await safe_send(websocket,{
            "type": "avatar_state",
            "state": "idle"
        })
    except Exception as e:
        print(f"[FAREWELL ERROR] {e}")


async def handle_device_register(websocket: WebSocket, message: dict, client_id: int, profile_id: str = "default"):
    device_id = message.get("device_id", "unknown")
    device_type = message.get("type", "unknown")
    client_devices[client_id] = device_id

    if device_type == "phone":
        from app.services.wearable_service import wearable_service, WearableDevice
        wd = WearableDevice(
            id=device_id,
            name=message.get("name", "Phone"),
            type="phone",
            platform=message.get("platform", "android"),
            is_online=True,
        )
        await wearable_service.register_device(wd, user_id=profile_id)

    await safe_send(websocket,{
        "type": "device_registered",
        "device_id": device_id,
        "device_type": device_type,
        "server_time": datetime.now(timezone.utc).isoformat(),
    })

    await broadcast({
        "type": "device_connected",
        "device_id": device_id,
        "name": message.get("name", "Unknown Device"),
        "platform": message.get("platform", "unknown"),
        "type": message.get("type", "unknown"),
    }, websocket)


async def handle_device_heartbeat(websocket: WebSocket, message: dict):
    device_id = message.get("device_id", "unknown")

    await safe_send(websocket,{
        "type": "heartbeat_ack",
        "device_id": device_id,
        "server_time": datetime.now(timezone.utc).isoformat(),
    })

    await broadcast({
        "type": "device_heartbeat",
        "device_id": device_id,
        "battery": message.get("battery"),
        "signal": message.get("signal"),
        "status": message.get("status", "online"),
    }, websocket)


async def handle_device_status_update(websocket: WebSocket, message: dict):
    await broadcast({
        "type": "device_status_update",
        "device_id": message.get("device_id"),
        "status": message.get("status"),
        "battery": message.get("battery"),
        "signal": message.get("signal"),
    }, websocket)


async def handle_text_message(websocket: WebSocket, message: dict, profile_id: str = "default"):
    from app.services.voice_profile_service import voice_profile_service

    await safe_send(websocket,{
        "type": "avatar_state",
        "state": "thinking"
    })

    try:
        if id(websocket) in introduction_pending:
            introduction_pending.discard(id(websocket))
            pdata = personality_service.get_profile(profile_id)
            text = message.get("text", "").strip().strip(".").strip()
            name = " ".join(w.capitalize() for w in text.split() if w.isalpha())
            if name and len(name) < 30:
                pdata.preferred_name = name
                pdata.introduced = True
                pdata._save()
                response_text = f"Nice to meet you, {name}! I will remember that. How may I assist you today?"
            else:
                pdata.preferred_name = "Boss"
                pdata.introduced = True
                pdata._save()
                response_text = "No problem! I will call you Boss. How may I assist you today?"
            profile = voice_profile_service.get_active_profile()
            tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice, rate=profile.rate, pitch=profile.pitch)
            await safe_send(websocket,{"type": "avatar_state", "state": "speaking"})
            await safe_send(websocket,{
                "type": "voice_response",
                "transcription": text,
                "response": response_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "introduction",
                "is_introduction": True,
            })
            await safe_send(websocket,{"type": "avatar_state", "state": "idle"})
            return

        text = message.get("text", "")

        command_result = command_registry.parse_command(text)
        if command_result["matched"]:
            pdata = personality_service.get_profile(profile_id)
            if command_result["handler"] == "goodbye":
                farewell_text = f"Goodbye, {pdata.preferred_name}. It was a pleasure assisting you."
                profile = voice_profile_service.get_active_profile()
                tts_audio = await voice_service.text_to_speech(
                    farewell_text,
                    voice=profile.voice,
                    rate=profile.rate,
                    pitch=profile.pitch,
                )

                await safe_send(websocket,{
                    "type": "avatar_state",
                    "state": "speaking"
                })

                await safe_send(websocket,{
                    "type": "voice_response",
                    "transcription": text,
                    "response": farewell_text,
                    "audio": base64.b64encode(tts_audio).decode(),
                    "model": "farewell",
                    "is_farewell": True,
                    "exit_app": True,
                })
                return

            execution = await command_registry.execute_command(text)

            result_data = execution.get("result", {})
            result_message = result_data.get("message", "Command executed.")
            extra_info = ""
            for k, v in result_data.items():
                if k not in ("status", "message") and v:
                    if isinstance(v, list):
                        extra_info += f"\n{k}: {', '.join(str(i) for i in v[:10])}"
                    elif isinstance(v, str) and len(v) > 5:
                        extra_info += f"\n{k}: {v}"
                    elif isinstance(v, dict):
                        extra_info += f"\n{k}: {json.dumps(v, indent=None)[:500]}"

            profile = voice_profile_service.get_active_profile()
            try:
                llm_response = await voice_service.chat_completion(
                    message=f"The user said: \"{text}\"\nCommand result: {result_message}{extra_info}\n\nRespond with a short natural sentence (1-2 lines) about what was done. Be helpful and conversational.",
                    system_prompt=_build_system_prompt("Keep responses under 2 sentences.", text, profile_id),
                    profile_id=profile_id,
                )
                response_text = llm_response["response"]
            except:
                response_text = result_message if result_message and result_message != "Command executed." else "All done."

            tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice)

            await safe_send(websocket,{
                "type": "command_response",
                "text": text,
                "command": command_result,
                "result": execution,
            })

            await safe_send(websocket,{
                "type": "avatar_state",
                "state": "speaking"
            })

            await safe_send(websocket,{
                "type": "voice_response",
                "transcription": text,
                "response": response_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "command_registry",
                "is_command": True,
            })

            await safe_send(websocket,{
                "type": "avatar_state",
                "state": "idle"
            })
            return

        llm_result = await command_registry.llm_parse_command(text)
        if llm_result and llm_result.get("handler"):
            handler = command_registry.handlers.get(llm_result["handler"])
            if handler:
                try:
                    params = llm_result.get("params", [])
                    execution_result = await handler(*params)

                    result_message = execution_result.get("message", "Command executed.")
                    extra_info = ""
                    for k, v in execution_result.items():
                        if k not in ("status", "message") and v:
                            if isinstance(v, list):
                                extra_info += f"\n{k}: {', '.join(str(i) for i in v[:10])}"
                            elif isinstance(v, str) and len(v) > 5:
                                extra_info += f"\n{k}: {v}"
                            elif isinstance(v, dict):
                                extra_info += f"\n{k}: {json.dumps(v, indent=None)[:500]}"

                    profile = voice_profile_service.get_active_profile()
                    try:
                        llm_response = await voice_service.chat_completion(
                            message=f"The user said: \"{text}\"\nCommand executed: {llm_result.get('handler', 'unknown')}\nResult: {result_message}{extra_info}\n\nGenerate a brief natural response about what just happened. Never say 'Command executed' or 'Done'. Say something a human assistant would say, like 'I've opened Brave for you' or 'Here are your folders' or 'Muted your PC'. One sentence max.",
                            system_prompt=_build_system_prompt("You just executed a system command for the user. Respond naturally in 1 sentence. Never use robotic phrases like 'command executed' or 'task completed'.", text, profile_id),
                            profile_id=profile_id,
                        )
                        response_text = llm_response["response"]
                    except:
                        response_text = result_message if result_message and result_message != "Command executed." else "All done."

                    tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice)

                    await safe_send(websocket,{
                        "type": "command_response",
                        "text": text,
                        "command": {"handler": llm_result["handler"], "params": params},
                        "result": execution_result,
                    })

                    await safe_send(websocket,{
                        "type": "avatar_state",
                        "state": "speaking"
                    })

                    await safe_send(websocket,{
                        "type": "voice_response",
                        "transcription": text,
                        "response": response_text,
                        "audio": base64.b64encode(tts_audio).decode(),
                        "model": "llm_command",
                        "is_command": True,
                    })

                    await safe_send(websocket,{
                        "type": "avatar_state",
                        "state": "idle"
                    })
                    return
                except Exception as e:
                    print(f"[LLM COMMAND ERROR] {e}")

        result = await voice_service.chat_completion(
            message=text,
            system_prompt=_build_system_prompt(user_message=text, profile_id=profile_id),
            conversation_history=message.get("conversation_history"),
            profile_id=profile_id,
        )

        profile = voice_profile_service.get_active_profile()
        tts_audio = await voice_service.text_to_speech(
            result["response"],
            voice=profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        await safe_send(websocket,{
            "type": "avatar_state",
            "state": "speaking"
        })

        await safe_send(websocket,{
            "type": "voice_response",
            "transcription": text,
            "response": result["response"],
            "audio": base64.b64encode(tts_audio).decode(),
            "model": result["model"],
        })

        await safe_send(websocket,{
            "type": "avatar_state",
            "state": "idle"
        })

    except Exception as e:
        try:
            error_text = f"I encountered an error: {type(e).__name__}. {e}"
            profile = voice_profile_service.get_active_profile()
            tts_audio = await voice_service.text_to_speech(error_text, voice=profile.voice)

            await safe_send(websocket,{
                "type": "avatar_state",
                "state": "speaking"
            })

            await safe_send(websocket,{
                "type": "voice_response",
                "response": error_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "error",
            })

            await safe_send(websocket,{
                "type": "avatar_state",
                "state": "idle"
            })
        except:
            await safe_send(websocket,{
                "type": "error",
                "message": str(e)
            })
            await safe_send(websocket,{
                "type": "avatar_state",
                "state": "error"
            })


async def handle_screen_start(websocket: WebSocket, message: dict):
    device_id = message.get("device_id", "unknown")
    session = screen_share_service.start_session(
        device_id=device_id,
        source=message.get("source", "pc"),
        fps=message.get("fps", 5),
        quality=message.get("quality", 80),
        width=message.get("width", 720),
        height=message.get("height", 1280),
    )

    await safe_send(websocket,{
        "type": "screen_started",
        "session_id": session.id,
        "device_id": device_id,
        "capture": {
            "fps": session.capture.fps,
            "quality": session.capture.quality,
            "width": session.capture.width,
            "height": session.capture.height,
        },
    })

    await broadcast({
        "type": "screen_session_available",
        "session_id": session.id,
        "device_id": device_id,
        "source": session.source,
    }, websocket)


async def handle_screen_stop(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    if not session_id:
        session = screen_share_service.get_session_by_device(
            message.get("device_id", "")
        )
        if session:
            session_id = session.id

    if session_id:
        screen_share_service.stop_session(session_id)
        await safe_send(websocket,{
            "type": "screen_stopped",
            "session_id": session_id,
        })
        await broadcast({
            "type": "screen_session_ended",
            "session_id": session_id,
        })


async def handle_screen_frame(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    frame_data = message.get("frame")

    if not session_id or not frame_data:
        return

    screen_share_service.record_frame(session_id)

    for client, viewer_sid in client_viewer_sessions.items():
        if viewer_sid == session_id:
            try:
                await client.send_json({
                    "type": "screen_frame",
                    "session_id": session_id,
                    "frame": frame_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except:
                pass


async def handle_screen_view(websocket: WebSocket, message: dict, client_id: int):
    session_id = message.get("session_id")
    if not session_id:
        await safe_send(websocket,{
            "type": "error",
            "message": "session_id required",
        })
        return

    session = screen_share_service.get_session(session_id)
    if not session:
        await safe_send(websocket,{
            "type": "error",
            "message": "Session not found",
        })
        return

    viewer_count = screen_share_service.add_viewer(session_id, str(client_id))
    client_viewer_sessions[client_id] = session_id

    await safe_send(websocket,{
        "type": "screen_viewing",
        "session_id": session_id,
        "device_id": session.device_id,
        "viewer_count": viewer_count,
        "capture": {
            "fps": session.capture.fps,
            "quality": session.capture.quality,
            "width": session.capture.width,
            "height": session.capture.height,
        },
    })

    device_id = session.device_id
    for client, dev_id in client_devices.items():
        if dev_id == device_id:
            try:
                await client.send_json({
                    "type": "screen_viewer_joined",
                    "session_id": session_id,
                    "viewer_count": viewer_count,
                })
            except:
                pass


async def handle_screen_unview(websocket: WebSocket, message: dict, client_id: int):
    session_id = client_viewer_sessions.pop(client_id, None)
    if session_id:
        viewer_count = screen_share_service.remove_viewer(session_id, str(client_id))
        await safe_send(websocket,{
            "type": "screen_unviewing",
            "session_id": session_id,
            "viewer_count": viewer_count,
        })


async def handle_screen_analyze(websocket: WebSocket, message: dict, profile_id: str = "default"):
    session_id = message.get("session_id")
    prompt = message.get("prompt", "Describe what is on this screen")
    frame_data = message.get("frame")

    if not frame_data:
        await safe_send(websocket,{
            "type": "screen_analysis",
            "session_id": session_id,
            "status": "error",
            "message": "No frame provided for analysis",
        })
        return

    try:
        frame_bytes = base64.b64decode(frame_data)
        result = await voice_service.chat_completion(
            message=f"[Screen Analysis Request]\n{prompt}\n\nNote: This is a placeholder response. Full OCR/vision analysis will be added with llava:7b integration.",
            system_prompt="You are J.A.R.V.I.S. analyzing a screen capture. Describe what you see.",
            profile_id=profile_id,
        )

        await safe_send(websocket,{
            "type": "screen_analysis",
            "session_id": session_id,
            "status": "complete",
            "description": result["response"],
            "model": result["model"],
        })
    except Exception as e:
        await safe_send(websocket,{
            "type": "screen_analysis",
            "session_id": session_id,
            "status": "error",
            "message": str(e),
        })


async def handle_camera_view(websocket: WebSocket, message: dict, client_id: int):
    camera_id = message.get("camera_id")
    if not camera_id:
        await safe_send(websocket,{
            "type": "error",
            "message": "camera_id required",
        })
        return

    session = rtsp_service.get_camera(camera_id)
    if not session:
        await safe_send(websocket,{
            "type": "error",
            "message": "Camera not found",
        })
        return

    viewer_count = rtsp_service.add_viewer(camera_id, str(client_id))
    client_camera_viewers[client_id] = camera_id

    await safe_send(websocket,{
        "type": "camera_viewing",
        "camera_id": camera_id,
        "name": session.config.name,
        "viewer_count": viewer_count,
        "fps": session.fps,
    })


async def handle_camera_unview(websocket: WebSocket, message: dict, client_id: int):
    camera_id = client_camera_viewers.pop(client_id, None)
    if camera_id:
        viewer_count = rtsp_service.remove_viewer(camera_id, str(client_id))
        await safe_send(websocket,{
            "type": "camera_unviewing",
            "camera_id": camera_id,
            "viewer_count": viewer_count,
        })


async def handle_camera_frame_request(websocket: WebSocket, message: dict):
    camera_id = message.get("camera_id")
    if not camera_id:
        await safe_send(websocket,{
            "type": "error",
            "message": "camera_id required",
        })
        return

    frame = await rtsp_service.capture_frame(camera_id)
    if not frame:
        await safe_send(websocket,{
            "type": "camera_frame",
            "camera_id": camera_id,
            "status": "error",
            "message": "Cannot capture frame",
        })
        return

    await safe_send(websocket,{
        "type": "camera_frame",
        "camera_id": camera_id,
        "frame": frame,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def handle_wearable_subscribe(websocket: WebSocket, message: dict, client_id: int):
    device_id = message.get("device_id")
    metrics = message.get("metrics", ["heart_rate", "spo2", "steps", "sleep"])

    wearable_service.subscribe(str(client_id), metrics)

    await safe_send(websocket,{
        "type": "wearable_subscribed",
        "device_id": device_id,
        "metrics": metrics,
    })


async def handle_wearable_unsubscribe(websocket: WebSocket, message: dict, client_id: int):
    wearable_service.unsubscribe(str(client_id))

    await safe_send(websocket,{
        "type": "wearable_unsubscribed",
    })


async def handle_wearable_health_update(websocket: WebSocket, message: dict):
    device_id = message.get("device_id")
    metric = message.get("metric")
    value = message.get("value")
    unit = message.get("unit", "")

    if not device_id or not metric:
        return

    await wearable_service.record_metric(device_id, metric, value, unit)

    for client_id_str in wearable_service.get_subscribers():
        for info_list in connected_clients.values():
            for info in info_list:
                if str(info.client_id) == client_id_str:
                    try:
                        await info.ws.send_json({
                            "type": "wearable_health_data",
                            "device_id": device_id,
                            "metric": metric,
                            "value": value,
                            "unit": unit,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    except:
                        pass


async def handle_vision_analyze(websocket: WebSocket, message: dict):
    camera_id = message.get("camera_id")
    prompt = message.get("prompt")
    context = message.get("context")

    if not camera_id:
        await safe_send(websocket,{
            "type": "error",
            "message": "camera_id required",
        })
        return

    await safe_send(websocket,{
        "type": "avatar_state",
        "state": "thinking"
    })

    result = await vision_service.analyze_frame(
        camera_id=camera_id,
        prompt=prompt,
        context=context,
    )

    await safe_send(websocket,{
        "type": "vision_result",
        "camera_id": camera_id,
        "result": result,
    })

    await safe_send(websocket,{
        "type": "avatar_state",
        "state": "idle"
    })


async def handle_vision_quick_look(websocket: WebSocket, message: dict):
    camera_id = message.get("camera_id")
    if not camera_id:
        await safe_send(websocket,{
            "type": "error",
            "message": "camera_id required",
        })
        return

    await safe_send(websocket,{
        "type": "avatar_state",
        "state": "thinking"
    })

    result = await vision_service.quick_look(camera_id)

    await safe_send(websocket,{
        "type": "vision_result",
        "camera_id": camera_id,
        "result": result,
    })

    await safe_send(websocket,{
        "type": "avatar_state",
        "state": "idle"
    })


async def handle_vision_scan_all(websocket: WebSocket):
    await safe_send(websocket,{
        "type": "avatar_state",
        "state": "thinking"
    })

    results = await vision_service.scan_all_cameras()

    await safe_send(websocket,{
        "type": "vision_scan_result",
        "results": results,
    })

    await safe_send(websocket,{
        "type": "avatar_state",
        "state": "idle"
    })


async def handle_vision_observe_start(websocket: WebSocket, message: dict):
    from app.services.vision_service import ObservationConfig, ObservationMode

    session_id = message.get("session_id", f"ws_{id(websocket)}")
    camera_ids = message.get("camera_ids", [])
    mode = message.get("mode", "watch")
    interval = message.get("interval", 10.0)

    if not camera_ids:
        await safe_send(websocket,{
            "type": "error",
            "message": "camera_ids required",
        })
        return

    config = ObservationConfig(
        camera_ids=camera_ids,
        mode=ObservationMode(mode),
        interval=interval,
        alert_on_motion=message.get("alert_on_motion", True),
        alert_on_person=message.get("alert_on_person", True),
        track_people=message.get("track_people", True),
        custom_prompt=message.get("custom_prompt", ""),
    )

    result = await vision_service.start_observation(session_id, config)

    vision_service.on_observation(lambda obs: asyncio.create_task(
        websocket.send_json({
            "type": "vision_observation",
            "session_id": session_id,
            "camera": obs.camera_name,
            "description": obs.description,
            "people_count": obs.people_count,
            "people_actions": obs.people_actions,
            "motion": obs.motion_detected,
            "timestamp": obs.timestamp,
        })
    ))

    vision_service.on_alert(lambda obs: asyncio.create_task(
        websocket.send_json({
            "type": "vision_alert",
            "session_id": session_id,
            "camera": obs.camera_name,
            "alerts": obs.alerts,
            "description": obs.description,
            "timestamp": obs.timestamp,
        })
    ))

    await safe_send(websocket,{
        "type": "vision_observe_started",
        "session_id": session_id,
        "result": result,
    })


async def handle_vision_observe_stop(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    if not session_id:
        await safe_send(websocket,{
            "type": "error",
            "message": "session_id required",
        })
        return

    result = await vision_service.stop_observation(session_id)

    await safe_send(websocket,{
        "type": "vision_observe_stopped",
        "session_id": session_id,
        "result": result,
    })


async def handle_voice_profile_switch(websocket: WebSocket, message: dict):
    from app.services.voice_profile_service import voice_profile_service

    profile_id = message.get("profile_id")
    if not profile_id:
        await safe_send(websocket,{
            "type": "error",
            "message": "profile_id required",
        })
        return

    result = voice_profile_service.set_active(profile_id)
    await safe_send(websocket,{
        "type": "voice_profile_changed",
        "result": result,
    })


async def handle_personality_update(websocket: WebSocket, message: dict, profile_id: str = "default"):
    update_type = message.get("update_type")

    if update_type == "style":
        result = personality_service.update_style(profile_id=profile_id, **{
            k: v for k, v in message.items()
            if k in ["formality", "humor", "verbosity", "empathy", "directness", "enthusiasm"]
        })
    elif update_type == "opinion":
        result = personality_service.learn_opinion(
            message.get("topic", ""),
            message.get("stance", ""),
            profile_id=profile_id,
        )
    elif update_type == "preference":
        result = personality_service.learn_preference(
            message.get("key", ""),
            message.get("value", ""),
            profile_id=profile_id,
        )
    elif update_type == "feedback":
        result = personality_service.adjust_from_feedback(message.get("feedback_type", ""), profile_id=profile_id)
    elif update_type == "name":
        pdata = personality_service.get_profile(profile_id)
        pdata.preferred_name = message.get("name", "Boss")
        pdata._save()
        result = {"status": "updated", "name": pdata.preferred_name}
    else:
        result = {"status": "error", "message": f"Unknown update type: {update_type}"}

    await safe_send(websocket,{
        "type": "personality_updated",
        "result": result,
    })


async def handle_browser_create_session(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    viewport_width = message.get("viewport_width", 1280)
    viewport_height = message.get("viewport_height", 720)

    session = await hermes_browser.create_session(
        session_id=session_id,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
    )

    await safe_send(websocket,{
        "type": "browser_session_created",
        "session_id": session.session_id,
        "created_at": session.created_at,
    })


async def handle_browser_destroy_session(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    if session_id:
        await hermes_browser.destroy_session(session_id)

    await safe_send(websocket,{
        "type": "browser_session_destroyed",
        "session_id": session_id,
    })


async def handle_browser_navigate(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    url = message.get("url")

    if not url:
        await safe_send(websocket,{
            "type": "error",
            "message": "url required",
        })
        return

    await safe_send(websocket,{
        "type": "browser_navigating",
        "session_id": session_id,
        "url": url,
    })

    result = await hermes_browser.navigate(session_id, url)

    await safe_send(websocket,{
        "type": "browser_navigate_result",
        "session_id": session_id,
        "result": result,
    })

    if result["status"] == "success":
        screenshot_result = await hermes_browser.screenshot(session_id)
        if screenshot_result["status"] == "success":
            await safe_send(websocket,{
                "type": "browser_screenshot",
                "session_id": session_id,
                "screenshot": screenshot_result["screenshot"],
                "url": screenshot_result["url"],
                "title": screenshot_result["title"],
            })


async def handle_browser_click(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    ref = message.get("ref")

    if not ref:
        await safe_send(websocket,{
            "type": "error",
            "message": "ref required",
        })
        return

    result = await hermes_browser.click(session_id, ref)

    await safe_send(websocket,{
        "type": "browser_click_result",
        "session_id": session_id,
        "result": result,
    })

    if result["status"] == "success":
        screenshot_result = await hermes_browser.screenshot(session_id)
        if screenshot_result["status"] == "success":
            await safe_send(websocket,{
                "type": "browser_screenshot",
                "session_id": session_id,
                "screenshot": screenshot_result["screenshot"],
                "url": screenshot_result["url"],
                "title": screenshot_result["title"],
            })


async def handle_browser_type(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    ref = message.get("ref")
    text = message.get("text")

    if not ref or text is None:
        await safe_send(websocket,{
            "type": "error",
            "message": "ref and text required",
        })
        return

    result = await hermes_browser.type_text(session_id, ref, text)

    await safe_send(websocket,{
        "type": "browser_type_result",
        "session_id": session_id,
        "result": result,
    })


async def handle_browser_screenshot(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")

    result = await hermes_browser.screenshot(session_id)

    await safe_send(websocket,{
        "type": "browser_screenshot",
        "session_id": session_id,
        "screenshot": result.get("screenshot"),
        "url": result.get("url"),
        "title": result.get("title"),
        "status": result["status"],
    })


async def handle_browser_snapshot(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")

    result = await hermes_browser.get_snapshot(session_id)

    await safe_send(websocket,{
        "type": "browser_snapshot",
        "session_id": session_id,
        "result": result,
    })


async def handle_browser_scroll(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    direction = message.get("direction", "down")
    amount = message.get("amount", 500)

    result = await hermes_browser.scroll(session_id, direction, amount)

    await safe_send(websocket,{
        "type": "browser_scroll_result",
        "session_id": session_id,
        "result": result,
    })


async def handle_browser_search(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    query = message.get("query")

    if not query:
        await safe_send(websocket,{
            "type": "error",
            "message": "query required",
        })
        return

    await safe_send(websocket,{
        "type": "browser_searching",
        "session_id": session_id,
        "query": query,
    })

    result = await hermes_browser.search_google(session_id, query)

    await safe_send(websocket,{
        "type": "browser_search_result",
        "session_id": session_id,
        "result": result,
    })

    if result["status"] == "success":
        screenshot_result = await hermes_browser.screenshot(session_id)
        if screenshot_result["status"] == "success":
            await safe_send(websocket,{
                "type": "browser_screenshot",
                "session_id": session_id,
                "screenshot": screenshot_result["screenshot"],
                "url": screenshot_result["url"],
                "title": screenshot_result["title"],
            })


async def handle_browser_get_state(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    
    if session_id:
        result = hermes_browser.get_tab_info(session_id)
    else:
        result = await hermes_browser.get_all_tabs_info()
    
    state_text = hermes_browser.get_browser_state_for_llm()
    
    await safe_send(websocket,{
        "type": "browser_state",
        "session_id": session_id,
        "state": result,
        "state_text": state_text,
    })


async def handle_browser_new_tab(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    url = message.get("url", "about:blank")
    
    result = await hermes_browser.new_tab(session_id, url)
    
    await safe_send(websocket,{
        "type": "browser_new_tab_result",
        "session_id": session_id,
        "result": result,
    })
    
    if result["status"] == "success":
        screenshot_result = await hermes_browser.screenshot(session_id)
        if screenshot_result["status"] == "success":
            await safe_send(websocket,{
                "type": "browser_screenshot",
                "session_id": session_id,
                "screenshot": screenshot_result["screenshot"],
                "url": screenshot_result["url"],
                "title": screenshot_result["title"],
            })


async def handle_browser_switch_tab(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    tab_index = message.get("tab_index", 0)
    
    result = await hermes_browser.switch_tab(session_id, tab_index)
    
    await safe_send(websocket,{
        "type": "browser_switch_tab_result",
        "session_id": session_id,
        "result": result,
    })
    
    if result["status"] == "success":
        screenshot_result = await hermes_browser.screenshot(session_id)
        if screenshot_result["status"] == "success":
            await safe_send(websocket,{
                "type": "browser_screenshot",
                "session_id": session_id,
                "screenshot": screenshot_result["screenshot"],
                "url": screenshot_result["url"],
                "title": screenshot_result["title"],
            })


async def handle_browser_close_tab(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    tab_index = message.get("tab_index")
    
    result = await hermes_browser.close_tab(session_id, tab_index)
    
    await safe_send(websocket,{
        "type": "browser_close_tab_result",
        "session_id": session_id,
        "result": result,
    })
    
    if result["status"] == "success":
        screenshot_result = await hermes_browser.screenshot(session_id)
        if screenshot_result["status"] == "success":
            await safe_send(websocket,{
                "type": "browser_screenshot",
                "session_id": session_id,
                "screenshot": screenshot_result["screenshot"],
                "url": screenshot_result["url"],
                "title": screenshot_result["title"],
            })


async def handle_browser_page_summary(websocket: WebSocket, message: dict):
    session_id = message.get("session_id", "default")
    
    result = await hermes_browser.get_page_summary(session_id)
    
    await safe_send(websocket,{
        "type": "browser_page_summary",
        "session_id": session_id,
        "result": result,
    })


async def handle_rag_ingest(websocket: WebSocket, message: dict):
    from app.services.rag_service import rag_service
    
    text = message.get("text", "")
    file_path = message.get("file_path", "")
    source = message.get("source", "websocket")
    
    if file_path:
        result = await asyncio.to_thread(rag_service.ingest_file, file_path)
    elif text:
        count = await asyncio.to_thread(rag_service.ingest_text, text, source)
        result = {"status": "success", "chunks_added": count}
    else:
        result = {"status": "error", "message": "Provide text or file_path"}
    
    await safe_send(websocket,{
        "type": "rag_ingest_result",
        "result": result,
    })


async def handle_rag_search(websocket: WebSocket, message: dict):
    from app.services.rag_service import rag_service
    
    query = message.get("query", "")
    top_k = message.get("top_k", 5)
    
    if not query:
        await safe_send(websocket,{
            "type": "error",
            "message": "query required",
        })
        return
    
    results = await asyncio.to_thread(rag_service.search, query, top_k, 0.3)
    context = await asyncio.to_thread(rag_service.get_context_for_llm, query, 3)
    
    await safe_send(websocket,{
        "type": "rag_search_result",
        "query": query,
        "results": results,
        "context": context,
    })


async def handle_rag_status(websocket: WebSocket):
    from app.services.rag_service import rag_service
    
    stats = await asyncio.to_thread(rag_service.get_stats)
    
    await safe_send(websocket,{
        "type": "rag_status",
        "stats": stats,
    })


async def handle_ocr_image(websocket: WebSocket, message: dict):
    from app.services.ocr_service import ocr_service
    
    image_b64 = message.get("image", "")
    prompt = message.get("prompt", "")
    mode = message.get("mode", "ocr")
    
    if not image_b64:
        await safe_send(websocket,{
            "type": "error",
            "message": "image (base64) required",
        })
        return
    
    if mode == "analyze":
        result = await ocr_service.analyze_image(image_b64, prompt or "Describe what you see in this image.")
    elif mode == "translate":
        result = await ocr_service.translate_text(image_b64, prompt or "english")
    elif mode == "describe":
        result = await ocr_service.describe_and_read(image_b64)
    else:
        result = await ocr_service.ocr_image(image_b64, prompt=prompt if prompt else None)
    
    await safe_send(websocket,{
        "type": "ocr_result",
        "mode": mode,
        "result": result,
    })


async def handle_ocr_screenshot(websocket: WebSocket, message: dict):
    from app.services.ocr_service import ocr_service
    
    prompt = message.get("prompt", "")
    
    await safe_send(websocket,{
        "type": "ocr_processing",
        "message": "Capturing and reading screen...",
    })
    
    result = await ocr_service.ocr_screenshot(prompt=prompt if prompt else None)
    
    await safe_send(websocket,{
        "type": "ocr_result",
        "mode": "screenshot",
        "result": result,
    })


# ── Monitoring WebSocket Handlers ──────────────────────────────────────────────

async def handle_monitoring_snapshot(websocket: WebSocket):
    from app.services.monitoring_service import monitoring_service
    snapshot = await asyncio.to_thread(monitoring_service.get_snapshot)
    await safe_send(websocket, {
        "type": "monitoring_snapshot",
        "data": snapshot,
    })


async def handle_monitoring_history(websocket: WebSocket, message: dict):
    from app.services.monitoring_service import monitoring_service
    minutes = message.get("minutes", 60)
    history = await asyncio.to_thread(monitoring_service.get_history, minutes)
    await safe_send(websocket, {
        "type": "monitoring_history",
        "data": history,
    })


async def handle_monitoring_alerts(websocket: WebSocket, message: dict):
    from app.services.alert_engine import alert_engine
    limit = message.get("limit", 20)
    alerts = await asyncio.to_thread(alert_engine.get_alert_history, limit)
    await safe_send(websocket, {
        "type": "monitoring_alerts",
        "alerts": alerts,
    })


async def handle_monitoring_thresholds(websocket: WebSocket):
    from app.services.monitoring_service import monitoring_service
    thresholds = monitoring_service.get_thresholds()
    await safe_send(websocket, {
        "type": "monitoring_thresholds",
        "thresholds": thresholds,
    })


async def handle_monitoring_set_threshold(websocket: WebSocket, message: dict):
    from app.services.monitoring_service import monitoring_service
    metric = message.get("metric", "")
    value = message.get("value", 0)
    monitoring_service.set_threshold(metric, value)
    await safe_send(websocket, {
        "type": "monitoring_threshold_set",
        "metric": metric,
        "value": value,
        "thresholds": monitoring_service.get_thresholds(),
    })


async def handle_activity_log(websocket: WebSocket, message: dict):
    from app.services.activity_logger import activity_logger
    limit = message.get("limit", 20)
    activity = await asyncio.to_thread(activity_logger.get_recent_activity, limit)
    await safe_send(websocket, {
        "type": "activity_log",
        "activity": activity,
    })


async def handle_activity_window(websocket: WebSocket, message: dict):
    from app.services.activity_logger import activity_logger
    minutes = message.get("minutes", 60)
    windows = await asyncio.to_thread(activity_logger.get_active_window_history, minutes)
    await safe_send(websocket, {
        "type": "activity_window_history",
        "windows": windows,
    })


async def handle_activity_processes(websocket: WebSocket):
    from app.services.activity_logger import activity_logger
    processes = await asyncio.to_thread(activity_logger.get_top_processes)
    await safe_send(websocket, {
        "type": "activity_processes",
        "processes": processes,
    })


# ── Briefing WebSocket Handlers ────────────────────────────────────────────────

async def handle_morning_briefing(websocket: WebSocket, message: dict):
    from app.services.briefing_service import briefing_service
    include_tts = message.get("include_tts", False)

    await safe_send(websocket, {
        "type": "briefing_status",
        "status": "generating",
        "message": "Assembling your briefing...",
    })

    result = await briefing_service.generate_briefing(include_tts=include_tts)

    await safe_send(websocket, {
        "type": "briefing_result",
        "data": result,
    })


async def handle_briefing_config(websocket: WebSocket, message: dict):
    from app.services.briefing_service import briefing_service
    sources = message.get("sources", {})
    if sources:
        briefing_service.configure(sources)
    await safe_send(websocket, {
        "type": "briefing_config",
        "config": briefing_service.get_config(),
    })


# ── Wake Word WebSocket Handlers ───────────────────────────────────────────────

voice_sessions: dict[int, VoiceSession] = {}


async def handle_voice_mode_start(websocket: WebSocket, profile_id: str):
    from app.services.settings_service import settings_service

    ws_id = id(websocket)
    if ws_id in voice_sessions:
        return
    try:
        threshold = float(settings_service.get(profile_id, "voice", "wake_word_sensitivity") or 0.5)
    except (TypeError, ValueError):
        threshold = 0.5
    session = VoiceSession(
        send=lambda payload: safe_send(websocket, payload),
        profile_id=profile_id,
        threshold=threshold,
        build_system_prompt=lambda message, pid: _build_system_prompt("", message, pid),
        is_introduction=lambda: ws_id in introduction_pending,
        on_intro_complete=lambda: introduction_pending.discard(ws_id),
    )
    result = await session.start()
    if result.get("status") == "success":
        voice_sessions[ws_id] = session


async def handle_audio_frame(websocket: WebSocket, message: dict):
    session = voice_sessions.get(id(websocket))
    if session is not None:
        await session.feed_pcm(message.get("audio", ""))


async def handle_tts_done(websocket: WebSocket):
    session = voice_sessions.get(id(websocket))
    if session is not None:
        await session.on_tts_done()


async def handle_voice_mode_stop(websocket: WebSocket):
    ws_id = id(websocket)
    session = voice_sessions.pop(ws_id, None)
    if session is not None:
        await session.stop()


async def handle_wake_word_config(websocket: WebSocket, message: dict):
    session = voice_sessions.get(id(websocket))
    if session is None:
        await safe_send(websocket, {"type": "wake_word_config", "config": {"active": False}})
        return
    sensitivity = message.get("sensitivity")
    if sensitivity is not None:
        session.set_threshold(float(sensitivity))
    keywords = message.get("keywords") or message.get("phrases")
    if keywords:
        session.set_keywords(keywords)
    await safe_send(websocket, {"type": "wake_word_config", "config": session.get_config()})


# ── Routine WebSocket Handlers ─────────────────────────────────────────────────

async def handle_run_routine(websocket: WebSocket, message: dict):
    from app.services.routine_service import routine_service

    async def on_progress(info):
        await safe_send(websocket, {
            "type": "routine_progress",
            "data": info,
        })

    routine_service.set_progress_callback(on_progress)
    name = message.get("name", "")

    await safe_send(websocket, {
        "type": "routine_started",
        "name": name,
    })

    result = await routine_service.run(name)

    await safe_send(websocket, {
        "type": "routine_result",
        "data": result,
    })


async def handle_create_routine(websocket: WebSocket, message: dict):
    from app.services.routine_service import routine_service
    import json as _json

    name = message.get("name", "")
    description = message.get("description", "")
    steps = message.get("steps", [])
    trigger_phrase = message.get("trigger_phrase", "")

    if isinstance(steps, str):
        try:
            steps = _json.loads(steps)
        except _json.JSONDecodeError:
            steps = []

    result = routine_service.create(name, description, steps, trigger_phrase)
    await safe_send(websocket, {
        "type": "routine_created",
        "data": result,
    })


async def handle_list_routines(websocket: WebSocket):
    from app.services.routine_service import routine_service
    routines = routine_service.get_all()
    await safe_send(websocket, {
        "type": "routine_list",
        "routines": routines,
    })


async def handle_delete_routine(websocket: WebSocket, message: dict):
    from app.services.routine_service import routine_service
    name = message.get("name", "")
    result = routine_service.delete(name)
    await safe_send(websocket, {
        "type": "routine_deleted",
        "data": result,
    })


# ── Email/Context/Notification WebSocket Handlers ──────────────────────────────

async def handle_check_email(websocket: WebSocket, message: dict):
    from app.services.email_service import email_service
    limit = message.get("limit", 5)
    query = message.get("query", "")
    emails = await email_service.get_recent(limit=limit, query=query)
    await safe_send(websocket, {
        "type": "email_list",
        "emails": emails,
    })


async def handle_email_summary(websocket: WebSocket, message: dict):
    from app.services.email_service import email_service
    limit = message.get("limit", 5)
    summary = await email_service.get_summary(limit=limit)
    await safe_send(websocket, {
        "type": "email_summary",
        "summary": summary,
    })


async def handle_screen_context(websocket: WebSocket, message: dict):
    from app.services.screen_context_service import screen_context_service
    prompt = message.get("prompt", "")
    result = await screen_context_service.capture_and_summarize(prompt)
    await safe_send(websocket, {
        "type": "screen_context",
        "data": result,
    })


async def handle_get_notifications(websocket: WebSocket, message: dict):
    from app.services.notification_service import notification_service
    limit = message.get("limit", 20)
    notifications = notification_service.get_recent(limit=limit)
    await safe_send(websocket, {
        "type": "notification_list",
        "notifications": notifications,
    })


# ── Suggestion WebSocket Handlers ──────────────────────────────────────────────

async def handle_get_suggestions(websocket: WebSocket):
    from app.services.suggestion_engine import suggestion_engine
    from app.services.monitoring_service import monitoring_service

    monitoring_data = monitoring_service.get_snapshot()
    suggestions = await suggestion_engine.evaluate(monitoring_data=monitoring_data)
    await safe_send(websocket, {
        "type": "suggestions",
        "suggestions": suggestions,
    })


async def handle_dismiss_suggestion(websocket: WebSocket, message: dict):
    from app.services.suggestion_engine import suggestion_engine
    suggestion_id = message.get("suggestion_id", "")
    suggestion_engine.dismiss(suggestion_id)
    await safe_send(websocket, {
        "type": "suggestion_dismissed",
        "suggestion_id": suggestion_id,
    })


# ── Personality WebSocket Handlers ─────────────────────────────────────────────

async def handle_personality_enhance(websocket: WebSocket, message: dict):
    from app.services.personality_enhancer import personality_enhancer
    text = message.get("text", "")
    context = message.get("context", "")
    enhanced = personality_enhancer.enhance_response(text, context)
    await safe_send(websocket, {
        "type": "personality_enhanced",
        "original": text,
        "enhanced": enhanced,
    })


async def handle_personality_config(websocket: WebSocket, message: dict):
    from app.services.personality_enhancer import personality_enhancer
    formality = message.get("formality")
    quip_frequency = message.get("quip_frequency")
    enabled = message.get("enabled")

    if formality is not None:
        personality_enhancer.set_formality(float(formality))
    if quip_frequency is not None:
        personality_enhancer.set_quip_frequency(float(quip_frequency))
    if enabled is not None:
        personality_enhancer.set_enabled(bool(enabled))

    await safe_send(websocket, {
        "type": "personality_config",
        "config": personality_enhancer.get_config(),
    })


# ── Device Mesh WebSocket Handlers ─────────────────────────────────────────────

async def handle_device_mesh_register(websocket: WebSocket, message: dict):
    from app.services.device_mesh_service import device_mesh_service
    device_id = message.get("device_id", "")
    device_info = message.get("device", {})
    if device_id:
        device_mesh_service.register_device(device_id, device_info)
    await safe_send(websocket, {
        "type": "mesh_registered",
        "device_id": device_id,
    })


async def handle_device_mesh_heartbeat(websocket: WebSocket, message: dict):
    from app.services.device_mesh_service import device_mesh_service
    device_id = message.get("device_id", "")
    if device_id:
        device_mesh_service.heartbeat(device_id)
    await safe_send(websocket, {
        "type": "mesh_heartbeat_ack",
    })


async def handle_push_to_device(websocket: WebSocket, message: dict):
    from app.services.device_mesh_service import device_mesh_service
    target = message.get("target_device", "")
    content = message.get("content", "")
    if target and content:
        device_mesh_service.queue_message(target, {
            "type": "push_message",
            "content": content,
            "from_device": message.get("device_id", "pc"),
        })
    await safe_send(websocket, {
        "type": "push_queued",
        "target_device": target,
    })


async def handle_sync_clipboard(websocket: WebSocket, message: dict):
    from app.services.device_mesh_service import device_mesh_service
    content = message.get("content")
    source = message.get("device_id", "pc")

    if content is not None:
        device_mesh_service.update_clipboard(content, source)

    clip = device_mesh_service.get_clipboard()
    await safe_send(websocket, {
        "type": "clipboard_sync",
        "clipboard": clip,
    })


async def handle_transfer_file(websocket: WebSocket, message: dict):
    from app.services.device_mesh_service import device_mesh_service
    file_path = message.get("file_path", "")
    target = message.get("target_device", "")

    result = await device_mesh_service.prepare_file_transfer(file_path, target)
    await safe_send(websocket, {
        "type": "transfer_ready",
        "data": result,
    })


async def handle_transfer_chunk(websocket: WebSocket, message: dict):
    from app.services.device_mesh_service import device_mesh_service
    transfer_id = message.get("transfer_id", "")
    offset = message.get("offset", 0)
    chunk_size = message.get("chunk_size", 65536)

    chunk = await device_mesh_service.read_file_chunk(transfer_id, offset, chunk_size)
    await safe_send(websocket, {
        "type": "transfer_chunk",
        "transfer_id": transfer_id,
        "data": chunk,
    })


async def handle_device_mesh_devices(websocket: WebSocket):
    from app.services.device_mesh_service import device_mesh_service
    devices = device_mesh_service.get_devices()
    await safe_send(websocket, {
        "type": "mesh_devices",
        "devices": devices,
    })


# ── Monitoring Alert Broadcast ─────────────────────────────────────────────────

async def _monitoring_alert_callback(alert: dict):
    await broadcast({
        "type": "system_alert",
        "alert": alert,
    })


def _setup_monitoring_broadcast():
    from app.services.monitoring_service import monitoring_service
    from app.services.alert_engine import alert_engine
    monitoring_service.add_listener(_monitoring_alert_callback)
    alert_engine.set_notification_callback(_monitoring_alert_callback)
