from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.screen_share_service import screen_share_service

router = APIRouter()


class StartSessionRequest(BaseModel):
    device_id: str
    source: str = "pc"
    fps: int = 5
    quality: int = 80
    width: int = 720
    height: int = 1280


class AnalyzeRequest(BaseModel):
    prompt: str = "Describe what is on this screen"


@router.get("/sessions")
async def list_sessions():
    sessions = screen_share_service.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = screen_share_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "device_id": session.device_id,
        "source": session.source,
        "status": session.status,
        "started_at": session.started_at.isoformat(),
        "capture": {
            "fps": session.capture.fps,
            "quality": session.capture.quality,
            "width": session.capture.width,
            "height": session.capture.height,
        },
        "viewer_count": session.viewer_count,
        "frame_count": session.frame_count,
    }


@router.post("/sessions")
async def start_session(req: StartSessionRequest):
    existing = screen_share_service.get_session_by_device(req.device_id)
    if existing and existing.status in ("active", "starting"):
        raise HTTPException(
            status_code=409,
            detail=f"Device already sharing in session {existing.id}",
        )

    session = screen_share_service.start_session(
        device_id=req.device_id,
        source=req.source,
        fps=req.fps,
        quality=req.quality,
        width=req.width,
        height=req.height,
    )
    return {
        "status": "started",
        "session_id": session.id,
        "device_id": session.device_id,
    }


@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: str):
    session = screen_share_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    screen_share_service.stop_session(session_id)
    return {"status": "stopped", "session_id": session_id}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    session = screen_share_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    screen_share_service.stop_session(session_id)
    screen_share_service.sessions.pop(session_id, None)
    return {"status": "deleted", "session_id": session_id}


@router.post("/sessions/{session_id}/analyze")
async def analyze_screen(session_id: str, req: AnalyzeRequest):
    session = screen_share_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "status": "analysis_requested",
        "prompt": req.prompt,
        "note": "Analysis will be performed on next frame via WebSocket",
    }
