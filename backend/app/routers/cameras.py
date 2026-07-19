from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.rtsp_service import rtsp_service, CameraConfig
import uuid

router = APIRouter()


class CameraCreate(BaseModel):
    name: str
    url: str
    username: Optional[str] = ""
    password: Optional[str] = ""
    type: str = "cctv"
    location: Optional[str] = ""


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None


@router.get("/")
async def get_cameras():
    return rtsp_service.get_all_cameras()


@router.get("/online")
async def get_online_cameras():
    return rtsp_service.get_online_cameras()


@router.get("/{camera_id}")
async def get_camera(camera_id: str):
    session = rtsp_service.get_camera(camera_id)
    if not session:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {
        "id": session.config.id,
        "name": session.config.name,
        "url": session.config.url,
        "type": session.config.type,
        "location": session.config.location,
        "is_online": session.config.is_online,
        "is_streaming": session.is_streaming,
        "viewer_count": len(session.viewers),
        "fps": session.fps,
    }


@router.post("/")
async def add_camera(camera: CameraCreate):
    camera_id = str(uuid.uuid4())[:8]
    config = CameraConfig(
        id=camera_id,
        name=camera.name,
        url=camera.url,
        username=camera.username,
        password=camera.password,
        type=camera.type,
        location=camera.location,
    )
    result = await rtsp_service.add_camera(config)
    return result


@router.put("/{camera_id}")
async def update_camera(camera_id: str, camera: CameraUpdate):
    session = rtsp_service.get_camera(camera_id)
    if not session:
        raise HTTPException(status_code=404, detail="Camera not found")

    if camera.name is not None:
        session.config.name = camera.name
    if camera.url is not None:
        session.config.url = camera.url
    if camera.username is not None:
        session.config.username = camera.username
    if camera.password is not None:
        session.config.password = camera.password
    if camera.type is not None:
        session.config.type = camera.type
    if camera.location is not None:
        session.config.location = camera.location

    return {"status": "updated", "camera_id": camera_id}


@router.delete("/{camera_id}")
async def delete_camera(camera_id: str):
    result = await rtsp_service.remove_camera(camera_id)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail="Camera not found")
    return result


@router.post("/{camera_id}/stream/start")
async def start_stream(camera_id: str, fps: int = 5, quality: int = 80):
    result = await rtsp_service.start_stream(camera_id, fps=fps, quality=quality)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{camera_id}/stream/stop")
async def stop_stream(camera_id: str):
    result = await rtsp_service.stop_stream(camera_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{camera_id}/snapshot")
async def take_snapshot(camera_id: str):
    frame = await rtsp_service.capture_frame(camera_id)
    if not frame:
        raise HTTPException(status_code=400, detail="Cannot capture frame")
    return {"camera_id": camera_id, "frame": frame}
