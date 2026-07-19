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

router = APIRouter()

connected_clients: list[WebSocket] = []


def _register_system_handlers():
    scs = system_command_service
    command_registry.register_handler("open_app", scs.open_app)
    command_registry.register_handler("open_browser", scs.open_browser)
    command_registry.register_handler("open_youtube", scs.open_youtube)
    command_registry.register_handler("play_youtube", scs.play_youtube)
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

    from app.services.knowledge_service import knowledge_service
    command_registry.register_handler("knowledge_summary", lambda: knowledge_service.get_stats())
    command_registry.register_handler("knowledge_search", knowledge_service.search)


_register_system_handlers()
client_devices: dict[int, str] = {}
client_viewer_sessions: dict[int, str] = {}
client_camera_viewers: dict[int, str] = {}
introduction_pending: set[int] = set()


async def broadcast(message: dict, exclude: WebSocket = None):
    for client in connected_clients:
        if client != exclude:
            try:
                await client.send_json(message)
            except:
                pass


async def send_to_device(device_id: str, message: dict):
    for client, dev_id in client_devices.items():
        if dev_id == device_id:
            try:
                await client.send_json(message)
            except:
                pass


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    client_id = id(websocket)

    try:
        await broadcast({
            "type": "client_connected",
            "client_id": client_id,
        }, websocket)

        # Send time-based greeting on connect
        await send_greeting(websocket)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "voice_chunk":
                await handle_voice_chunk(websocket, message)
            elif msg_type == "text_message":
                await handle_text_message(websocket, message)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "device_register":
                await handle_device_register(websocket, message, client_id)
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
                await handle_screen_analyze(websocket, message)
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
                await handle_personality_update(websocket, message)
            elif msg_type == "farewell":
                await handle_farewell(websocket)
            elif msg_type == "greeting":
                await send_greeting(websocket)
            else:
                await broadcast(message, websocket)

    except WebSocketDisconnect:
        introduction_pending.discard(client_id)
        connected_clients.remove(websocket)
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


async def send_greeting(websocket: WebSocket):
    from app.services.voice_service import voice_service
    from app.services.voice_profile_service import voice_profile_service
    from app.services.personality_service import personality_service

    try:
        if not personality_service.introduced:
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

            await websocket.send_json({
                "type": "avatar_state",
                "state": "speaking"
            })

            await websocket.send_json({
                "type": "voice_response",
                "response": intro_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "introduction",
                "is_introduction": True,
            })

            await websocket.send_json({
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

        greeting_text = f"Good {period}, {personality_service.preferred_name}. How may I assist you today?"

        profile = voice_profile_service.get_active_profile()
        tts_audio = await voice_service.text_to_speech(
            greeting_text,
            voice=profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        await websocket.send_json({
            "type": "avatar_state",
            "state": "speaking"
        })

        await websocket.send_json({
            "type": "voice_response",
            "response": greeting_text,
            "audio": base64.b64encode(tts_audio).decode(),
            "model": "greeting",
            "is_greeting": True,
        })

        await websocket.send_json({
            "type": "avatar_state",
            "state": "idle"
        })
    except Exception as e:
        print(f"[GREETING ERROR] {e}")


async def handle_farewell(websocket: WebSocket):
    from app.services.voice_service import voice_service
    from app.services.voice_profile_service import voice_profile_service
    from app.services.personality_service import personality_service

    try:
        hour = datetime.now().hour

        if 5 <= hour < 12:
            farewell_text = f"Good morning, {personality_service.preferred_name}. Have a productive day ahead."
        elif 12 <= hour < 17:
            farewell_text = f"Good afternoon, {personality_service.preferred_name}. I will be here when you need me."
        elif 17 <= hour < 21:
            farewell_text = f"Good evening, {personality_service.preferred_name}. Take care and I will see you later."
        else:
            farewell_text = f"Good night, {personality_service.preferred_name}. Sleep well and I will be ready when you return."

        profile = voice_profile_service.get_active_profile()
        tts_audio = await voice_service.text_to_speech(
            farewell_text,
            voice=profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        await websocket.send_json({
            "type": "avatar_state",
            "state": "speaking"
        })

        await websocket.send_json({
            "type": "voice_response",
            "response": farewell_text,
            "audio": base64.b64encode(tts_audio).decode(),
            "model": "farewell",
            "is_farewell": True,
        })

        await websocket.send_json({
            "type": "avatar_state",
            "state": "idle"
        })
    except Exception as e:
        print(f"[FAREWELL ERROR] {e}")


async def handle_device_register(websocket: WebSocket, message: dict, client_id: int):
    device_id = message.get("device_id", "unknown")
    client_devices[client_id] = device_id

    await websocket.send_json({
        "type": "device_registered",
        "device_id": device_id,
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

    await websocket.send_json({
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


async def handle_voice_chunk(websocket: WebSocket, message: dict):
    from app.services.voice_profile_service import voice_profile_service
    from app.services.personality_service import personality_service

    try:
        if id(websocket) in introduction_pending:
            introduction_pending.discard(id(websocket))
            audio_b64 = message.get("audio")
            if not audio_b64:
                return
            audio_data = base64.b64decode(audio_b64)
            stt_result = await voice_service.speech_to_text(audio_data)
            name = stt_result["text"].strip().strip(".").strip()
            name = " ".join(w.capitalize() for w in name.split() if w.isalpha())
            if name:
                personality_service.preferred_name = name
                personality_service.introduced = True
                personality_service._save()
                response_text = f"Nice to meet you, {name}! I will remember that. How may I assist you today?"
            else:
                personality_service.preferred_name = "Boss"
                personality_service.introduced = True
                personality_service._save()
                response_text = "No problem! I will call you Boss. How may I assist you today?"
            profile = voice_profile_service.get_active_profile()
            tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice, rate=profile.rate, pitch=profile.pitch)
            await websocket.send_json({"type": "avatar_state", "state": "speaking"})
            await websocket.send_json({
                "type": "voice_response",
                "transcription": stt_result["text"],
                "response": response_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "introduction",
                "is_introduction": True,
            })
            await websocket.send_json({"type": "avatar_state", "state": "idle"})
            return

        audio_b64 = message.get("audio")
        if not audio_b64:
            return

        audio_data = base64.b64decode(audio_b64)

        await websocket.send_json({
            "type": "avatar_state",
            "state": "thinking"
        })

        stt_result = await voice_service.speech_to_text(audio_data)
        transcription = stt_result["text"]

        command_result = command_registry.parse_command(transcription)
        if command_result["matched"]:
            if command_result["handler"] == "goodbye":
                farewell_text = f"Goodbye, {personality_service.preferred_name}. It was a pleasure assisting you."
                profile = voice_profile_service.get_active_profile()
                tts_audio = await voice_service.text_to_speech(
                    farewell_text,
                    voice=profile.voice,
                    rate=profile.rate,
                    pitch=profile.pitch,
                )

                await websocket.send_json({
                    "type": "avatar_state",
                    "state": "speaking"
                })

                await websocket.send_json({
                    "type": "voice_response",
                    "transcription": transcription,
                    "response": farewell_text,
                    "audio": base64.b64encode(tts_audio).decode(),
                    "model": "farewell",
                    "is_farewell": True,
                    "exit_app": True,
                })
                return

            execution = await command_registry.execute_command(transcription)

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
                    message=f"The user said: \"{transcription}\"\nCommand result: {result_message}{extra_info}\n\nRespond with a short natural sentence (1-2 lines) about what was done. Be helpful and conversational.",
                    system_prompt=f"You are JARVIS. {personality_service.get_system_prompt()}\nKeep responses under 2 sentences.",
                )
                response_text = llm_response["response"]
            except:
                response_text = result_message if result_message and result_message != "Command executed." else "All done."

            tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice)

            await websocket.send_json({
                "type": "command_response",
                "transcription": transcription,
                "command": command_result,
                "result": execution,
            })

            await websocket.send_json({
                "type": "avatar_state",
                "state": "speaking"
            })

            await websocket.send_json({
                "type": "voice_response",
                "transcription": transcription,
                "confidence": stt_result["confidence"],
                "response": response_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "command_registry",
                "is_command": True,
            })

            await websocket.send_json({
                "type": "avatar_state",
                "state": "idle"
            })
            return

        llm_result = await command_registry.llm_parse_command(transcription)
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
                            message=f"The user said: \"{transcription}\"\nCommand executed: {command_result.get('handler', 'unknown')}\nResult: {result_message}{extra_info}\n\nGenerate a brief natural response about what just happened. Never say 'Command executed' or 'Done'. Say something a human assistant would say, like 'I've opened Brave for you' or 'Here are your folders' or 'Muted your PC'. One sentence max.",
                            system_prompt=f"You are JARVIS, a sophisticated AI assistant. {personality_service.get_system_prompt()}\nYou just executed a system command for the user. Respond naturally in 1 sentence. Never use robotic phrases like 'command executed' or 'task completed'.",
                        )
                        response_text = llm_response["response"]
                    except:
                        response_text = result_message if result_message and result_message != "Command executed." else "All done."

                    tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice)

                    await websocket.send_json({
                        "type": "command_response",
                        "transcription": transcription,
                        "command": {"handler": llm_result["handler"], "params": params},
                        "result": execution_result,
                    })

                    await websocket.send_json({
                        "type": "avatar_state",
                        "state": "speaking"
                    })

                    await websocket.send_json({
                        "type": "voice_response",
                        "transcription": transcription,
                        "confidence": stt_result["confidence"],
                        "response": response_text,
                        "audio": base64.b64encode(tts_audio).decode(),
                        "model": "llm_command",
                        "is_command": True,
                    })

                    await websocket.send_json({
                        "type": "avatar_state",
                        "state": "idle"
                    })
                    return
                except Exception as e:
                    print(f"[LLM COMMAND ERROR] {e}")

        result = await voice_service.voice_pipeline(
            audio_data=audio_data,
            system_prompt=message.get("system_prompt"),
        )

        await websocket.send_json({
            "type": "avatar_state",
            "state": "speaking"
        })

        await websocket.send_json({
            "type": "voice_response",
            "transcription": transcription,
            "confidence": result["confidence"],
            "response": result["response"],
            "audio": base64.b64encode(result["audio"]).decode(),
            "model": result["model"]
        })

        await websocket.send_json({
            "type": "avatar_state",
            "state": "idle"
        })

    except Exception as e:
        print(f"[VOICE CHUNK ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        try:
            from app.services.voice_profile_service import voice_profile_service as _vps
            error_text = f"I encountered an error: {type(e).__name__}. {e}"
            profile = _vps.get_active_profile()
            tts_audio = await voice_service.text_to_speech(error_text, voice=profile.voice)

            await websocket.send_json({
                "type": "avatar_state",
                "state": "speaking"
            })

            await websocket.send_json({
                "type": "voice_response",
                "response": error_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "error",
            })

            await websocket.send_json({
                "type": "avatar_state",
                "state": "idle"
            })
        except:
            await websocket.send_json({
                "type": "error",
                "message": f"Something went wrong: {type(e).__name__}: {e}"
            })
            await websocket.send_json({
                "type": "avatar_state",
                "state": "error"
            })


async def handle_text_message(websocket: WebSocket, message: dict):
    from app.services.personality_service import personality_service
    from app.services.voice_profile_service import voice_profile_service

    await websocket.send_json({
        "type": "avatar_state",
        "state": "thinking"
    })

    try:
        if id(websocket) in introduction_pending:
            introduction_pending.discard(id(websocket))
            text = message.get("text", "").strip().strip(".").strip()
            name = " ".join(w.capitalize() for w in text.split() if w.isalpha())
            if name and len(name) < 30:
                personality_service.preferred_name = name
                personality_service.introduced = True
                personality_service._save()
                response_text = f"Nice to meet you, {name}! I will remember that. How may I assist you today?"
            else:
                personality_service.preferred_name = "Boss"
                personality_service.introduced = True
                personality_service._save()
                response_text = "No problem! I will call you Boss. How may I assist you today?"
            profile = voice_profile_service.get_active_profile()
            tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice, rate=profile.rate, pitch=profile.pitch)
            await websocket.send_json({"type": "avatar_state", "state": "speaking"})
            await websocket.send_json({
                "type": "voice_response",
                "transcription": text,
                "response": response_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "introduction",
                "is_introduction": True,
            })
            await websocket.send_json({"type": "avatar_state", "state": "idle"})
            return

        text = message.get("text", "")

        command_result = command_registry.parse_command(text)
        if command_result["matched"]:
            if command_result["handler"] == "goodbye":
                farewell_text = f"Goodbye, {personality_service.preferred_name}. It was a pleasure assisting you."
                profile = voice_profile_service.get_active_profile()
                tts_audio = await voice_service.text_to_speech(
                    farewell_text,
                    voice=profile.voice,
                    rate=profile.rate,
                    pitch=profile.pitch,
                )

                await websocket.send_json({
                    "type": "avatar_state",
                    "state": "speaking"
                })

                await websocket.send_json({
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
                    system_prompt=f"You are JARVIS. {personality_service.get_system_prompt()}\nKeep responses under 2 sentences.",
                )
                response_text = llm_response["response"]
            except:
                response_text = result_message if result_message and result_message != "Command executed." else "All done."

            tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice)

            await websocket.send_json({
                "type": "command_response",
                "text": text,
                "command": command_result,
                "result": execution,
            })

            await websocket.send_json({
                "type": "avatar_state",
                "state": "speaking"
            })

            await websocket.send_json({
                "type": "voice_response",
                "transcription": text,
                "response": response_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "command_registry",
                "is_command": True,
            })

            await websocket.send_json({
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
                            system_prompt=f"You are JARVIS, a sophisticated AI assistant. {personality_service.get_system_prompt()}\nYou just executed a system command for the user. Respond naturally in 1 sentence. Never use robotic phrases like 'command executed' or 'task completed'.",
                        )
                        response_text = llm_response["response"]
                    except:
                        response_text = result_message if result_message and result_message != "Command executed." else "All done."

                    tts_audio = await voice_service.text_to_speech(response_text, voice=profile.voice)

                    await websocket.send_json({
                        "type": "command_response",
                        "text": text,
                        "command": {"handler": llm_result["handler"], "params": params},
                        "result": execution_result,
                    })

                    await websocket.send_json({
                        "type": "avatar_state",
                        "state": "speaking"
                    })

                    await websocket.send_json({
                        "type": "voice_response",
                        "transcription": text,
                        "response": response_text,
                        "audio": base64.b64encode(tts_audio).decode(),
                        "model": "llm_command",
                        "is_command": True,
                    })

                    await websocket.send_json({
                        "type": "avatar_state",
                        "state": "idle"
                    })
                    return
                except Exception as e:
                    print(f"[LLM COMMAND ERROR] {e}")

        result = await voice_service.chat_completion(
            message=text,
            system_prompt=personality_service.get_system_prompt(),
            conversation_history=message.get("conversation_history")
        )

        profile = voice_profile_service.get_active_profile()
        tts_audio = await voice_service.text_to_speech(
            result["response"],
            voice=profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        await websocket.send_json({
            "type": "avatar_state",
            "state": "speaking"
        })

        await websocket.send_json({
            "type": "voice_response",
            "transcription": text,
            "response": result["response"],
            "audio": base64.b64encode(tts_audio).decode(),
            "model": result["model"],
        })

        await websocket.send_json({
            "type": "avatar_state",
            "state": "idle"
        })

    except Exception as e:
        try:
            error_text = f"I encountered an error: {type(e).__name__}. {e}"
            profile = voice_profile_service.get_active_profile()
            tts_audio = await voice_service.text_to_speech(error_text, voice=profile.voice)

            await websocket.send_json({
                "type": "avatar_state",
                "state": "speaking"
            })

            await websocket.send_json({
                "type": "voice_response",
                "response": error_text,
                "audio": base64.b64encode(tts_audio).decode(),
                "model": "error",
            })

            await websocket.send_json({
                "type": "avatar_state",
                "state": "idle"
            })
        except:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            await websocket.send_json({
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

    await websocket.send_json({
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
        await websocket.send_json({
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
        await websocket.send_json({
            "type": "error",
            "message": "session_id required",
        })
        return

    session = screen_share_service.get_session(session_id)
    if not session:
        await websocket.send_json({
            "type": "error",
            "message": "Session not found",
        })
        return

    viewer_count = screen_share_service.add_viewer(session_id, str(client_id))
    client_viewer_sessions[client_id] = session_id

    await websocket.send_json({
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
        await websocket.send_json({
            "type": "screen_unviewing",
            "session_id": session_id,
            "viewer_count": viewer_count,
        })


async def handle_screen_analyze(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    prompt = message.get("prompt", "Describe what is on this screen")
    frame_data = message.get("frame")

    if not frame_data:
        await websocket.send_json({
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
        )

        await websocket.send_json({
            "type": "screen_analysis",
            "session_id": session_id,
            "status": "complete",
            "description": result["response"],
            "model": result["model"],
        })
    except Exception as e:
        await websocket.send_json({
            "type": "screen_analysis",
            "session_id": session_id,
            "status": "error",
            "message": str(e),
        })


async def handle_camera_view(websocket: WebSocket, message: dict, client_id: int):
    camera_id = message.get("camera_id")
    if not camera_id:
        await websocket.send_json({
            "type": "error",
            "message": "camera_id required",
        })
        return

    session = rtsp_service.get_camera(camera_id)
    if not session:
        await websocket.send_json({
            "type": "error",
            "message": "Camera not found",
        })
        return

    viewer_count = rtsp_service.add_viewer(camera_id, str(client_id))
    client_camera_viewers[client_id] = camera_id

    await websocket.send_json({
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
        await websocket.send_json({
            "type": "camera_unviewing",
            "camera_id": camera_id,
            "viewer_count": viewer_count,
        })


async def handle_camera_frame_request(websocket: WebSocket, message: dict):
    camera_id = message.get("camera_id")
    if not camera_id:
        await websocket.send_json({
            "type": "error",
            "message": "camera_id required",
        })
        return

    frame = await rtsp_service.capture_frame(camera_id)
    if not frame:
        await websocket.send_json({
            "type": "camera_frame",
            "camera_id": camera_id,
            "status": "error",
            "message": "Cannot capture frame",
        })
        return

    await websocket.send_json({
        "type": "camera_frame",
        "camera_id": camera_id,
        "frame": frame,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def handle_wearable_subscribe(websocket: WebSocket, message: dict, client_id: int):
    device_id = message.get("device_id")
    metrics = message.get("metrics", ["heart_rate", "spo2", "steps", "sleep"])

    wearable_service.subscribe(str(client_id), metrics)

    await websocket.send_json({
        "type": "wearable_subscribed",
        "device_id": device_id,
        "metrics": metrics,
    })


async def handle_wearable_unsubscribe(websocket: WebSocket, message: dict, client_id: int):
    wearable_service.unsubscribe(str(client_id))

    await websocket.send_json({
        "type": "wearable_unsubscribed",
    })


async def handle_wearable_health_update(websocket: WebSocket, message: dict):
    device_id = message.get("device_id")
    metric = message.get("metric")
    value = message.get("value")
    unit = message.get("unit", "")

    if not device_id or not metric:
        return

    wearable_service.record_metric(device_id, metric, value, unit)

    for client_id_str in wearable_service.get_subscribers():
        for client in connected_clients:
            if str(id(client)) == client_id_str:
                try:
                    await client.send_json({
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
        await websocket.send_json({
            "type": "error",
            "message": "camera_id required",
        })
        return

    await websocket.send_json({
        "type": "avatar_state",
        "state": "thinking"
    })

    result = await vision_service.analyze_frame(
        camera_id=camera_id,
        prompt=prompt,
        context=context,
    )

    await websocket.send_json({
        "type": "vision_result",
        "camera_id": camera_id,
        "result": result,
    })

    await websocket.send_json({
        "type": "avatar_state",
        "state": "idle"
    })


async def handle_vision_quick_look(websocket: WebSocket, message: dict):
    camera_id = message.get("camera_id")
    if not camera_id:
        await websocket.send_json({
            "type": "error",
            "message": "camera_id required",
        })
        return

    await websocket.send_json({
        "type": "avatar_state",
        "state": "thinking"
    })

    result = await vision_service.quick_look(camera_id)

    await websocket.send_json({
        "type": "vision_result",
        "camera_id": camera_id,
        "result": result,
    })

    await websocket.send_json({
        "type": "avatar_state",
        "state": "idle"
    })


async def handle_vision_scan_all(websocket: WebSocket):
    await websocket.send_json({
        "type": "avatar_state",
        "state": "thinking"
    })

    results = await vision_service.scan_all_cameras()

    await websocket.send_json({
        "type": "vision_scan_result",
        "results": results,
    })

    await websocket.send_json({
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
        await websocket.send_json({
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

    await websocket.send_json({
        "type": "vision_observe_started",
        "session_id": session_id,
        "result": result,
    })


async def handle_vision_observe_stop(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    if not session_id:
        await websocket.send_json({
            "type": "error",
            "message": "session_id required",
        })
        return

    result = await vision_service.stop_observation(session_id)

    await websocket.send_json({
        "type": "vision_observe_stopped",
        "session_id": session_id,
        "result": result,
    })


async def handle_voice_profile_switch(websocket: WebSocket, message: dict):
    from app.services.voice_profile_service import voice_profile_service

    profile_id = message.get("profile_id")
    if not profile_id:
        await websocket.send_json({
            "type": "error",
            "message": "profile_id required",
        })
        return

    result = voice_profile_service.set_active(profile_id)
    await websocket.send_json({
        "type": "voice_profile_changed",
        "result": result,
    })


async def handle_personality_update(websocket: WebSocket, message: dict):
    from app.services.personality_service import personality_service

    update_type = message.get("update_type")

    if update_type == "style":
        result = personality_service.update_style(**{
            k: v for k, v in message.items()
            if k in ["formality", "humor", "verbosity", "empathy", "directness", "enthusiasm"]
        })
    elif update_type == "opinion":
        result = personality_service.learn_opinion(
            message.get("topic", ""),
            message.get("stance", ""),
        )
    elif update_type == "preference":
        result = personality_service.learn_preference(
            message.get("key", ""),
            message.get("value", ""),
        )
    elif update_type == "feedback":
        result = personality_service.adjust_from_feedback(message.get("feedback_type", ""))
    elif update_type == "name":
        personality_service.preferred_name = message.get("name", "Boss")
        personality_service._save()
        result = {"status": "updated", "name": personality_service.preferred_name}
    else:
        result = {"status": "error", "message": f"Unknown update type: {update_type}"}

    await websocket.send_json({
        "type": "personality_updated",
        "result": result,
    })
