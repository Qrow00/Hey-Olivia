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

router = APIRouter()

connected_clients: list[WebSocket] = []
client_devices: dict[int, str] = {}
client_viewer_sessions: dict[int, str] = {}
client_camera_viewers: dict[int, str] = {}


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
            else:
                await broadcast(message, websocket)

    except WebSocketDisconnect:
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
    await websocket.send_json({
        "type": "avatar_state",
        "state": "listening"
    })

    try:
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
            execution = await command_registry.execute_command(transcription)

            await websocket.send_json({
                "type": "command_response",
                "transcription": transcription,
                "command": command_result,
                "result": execution,
            })

            response_text = execution.get("result", {}).get("message", "Command executed.")
            tts_audio = await voice_service.text_to_speech(response_text)

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

        result = await voice_service.voice_pipeline(
            audio_data=audio_data,
            system_prompt=message.get("system_prompt", "You are J.A.R.V.I.S., a helpful AI assistant.")
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
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.send_json({
            "type": "avatar_state",
            "state": "error"
        })


async def handle_text_message(websocket: WebSocket, message: dict):
    await websocket.send_json({
        "type": "avatar_state",
        "state": "thinking"
    })

    try:
        text = message.get("text", "")

        command_result = command_registry.parse_command(text)
        if command_result["matched"]:
            execution = await command_registry.execute_command(text)

            await websocket.send_json({
                "type": "command_response",
                "text": text,
                "command": command_result,
                "result": execution,
            })

            response_text = execution.get("result", {}).get("message", "Command executed.")
            await websocket.send_json({
                "type": "text_response",
                "response": response_text,
                "model": "command_registry",
                "is_command": True,
            })

            await websocket.send_json({
                "type": "avatar_state",
                "state": "idle"
            })
            return

        result = await voice_service.chat_completion(
            message=text,
            system_prompt=message.get("system_prompt", "You are J.A.R.V.I.S., a helpful AI assistant."),
            conversation_history=message.get("conversation_history")
        )

        await websocket.send_json({
            "type": "text_response",
            "response": result["response"],
            "model": result["model"]
        })

        await websocket.send_json({
            "type": "avatar_state",
            "state": "idle"
        })

    except Exception as e:
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
