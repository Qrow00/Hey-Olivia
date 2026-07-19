from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.vision_service import vision_service, ObservationConfig, ObservationMode
from app.services.rtsp_service import rtsp_service

router = APIRouter()


class VisionQuery(BaseModel):
    camera_id: str
    prompt: Optional[str] = None
    context: Optional[str] = None


class ObservationStart(BaseModel):
    session_id: str
    camera_ids: List[str]
    mode: str = "watch"
    interval: float = 10.0
    alert_on_motion: bool = True
    alert_on_person: bool = True
    track_people: bool = True
    describe_scene: bool = True
    custom_prompt: Optional[str] = ""


@router.get("/cameras")
async def get_vision_cameras():
    cameras = rtsp_service.get_all_cameras()
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "is_online": c["is_online"],
            "location": c["location"],
        }
        for c in cameras
    ]


@router.post("/analyze")
async def analyze_camera(query: VisionQuery):
    result = await vision_service.analyze_frame(
        camera_id=query.camera_id,
        prompt=query.prompt,
        context=query.context,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/quick-look/{camera_id}")
async def quick_look(camera_id: str):
    result = await vision_service.quick_look(camera_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/describe")
async def describe_for_command(query: VisionQuery):
    result = await vision_service.describe_for_command(
        camera_id=query.camera_id,
        user_query=query.prompt or "What do you see?",
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/scan-all")
async def scan_all_cameras():
    results = await vision_service.scan_all_cameras()
    return {"cameras": results}


@router.post("/observe/start")
async def start_observation(obs: ObservationStart):
    config = ObservationConfig(
        camera_ids=obs.camera_ids,
        mode=ObservationMode(obs.mode),
        interval=obs.interval,
        alert_on_motion=obs.alert_on_motion,
        alert_on_person=obs.alert_on_person,
        track_people=obs.track_people,
        describe_scene=obs.describe_scene,
        custom_prompt=obs.custom_prompt or "",
    )
    result = await vision_service.start_observation(obs.session_id, config)
    return result


@router.post("/observe/stop/{session_id}")
async def stop_observation(session_id: str):
    result = await vision_service.stop_observation(session_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/observe/sessions")
async def get_observation_sessions():
    return vision_service.get_all_sessions()


@router.get("/observe/{session_id}")
async def get_observation_session(session_id: str):
    session = vision_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "mode": session.config.mode.value,
        "cameras": session.config.camera_ids,
        "is_active": session.is_active,
        "interval": session.config.interval,
        "last_observation": {
            "camera": session.last_observation.camera_name,
            "description": session.last_observation.description,
            "people_count": session.last_observation.people_count,
            "timestamp": session.last_observation.timestamp,
        } if session.last_observation else None,
    }


@router.get("/observe/{session_id}/history")
async def get_observation_history(session_id: str, limit: int = 10):
    history = vision_service.get_recent_observations(session_id, limit)
    return {"session_id": session_id, "observations": history}
