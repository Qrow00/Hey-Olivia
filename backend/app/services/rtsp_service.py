import asyncio
import base64
import time
from dataclasses import dataclass, field
from typing import Optional
import cv2
import numpy as np


@dataclass
class CameraConfig:
    id: str
    name: str
    url: str
    username: str = ""
    password: str = ""
    type: str = "cctv"
    location: str = ""
    is_online: bool = False
    last_frame_time: float = 0


@dataclass
class CameraSession:
    config: CameraConfig
    capture: Optional[cv2.VideoCapture] = None
    is_streaming: bool = False
    viewers: set = field(default_factory=set)
    fps: int = 5
    quality: int = 80


class RTSPService:
    def __init__(self):
        self.cameras: dict[str, CameraSession] = {}
        self._capture_tasks: dict[str, asyncio.Task] = {}

    def _build_rtsp_url(self, config: CameraConfig) -> str:
        if config.username and config.password:
            protocol = config.url.split("://")[0]
            rest = config.url.split("://")[1]
            return f"{protocol}://{config.username}:{config.password}@{rest}"
        return config.url

    async def add_camera(self, config: CameraConfig) -> dict:
        session = CameraSession(config=config)
        self.cameras[config.id] = session

        try:
            url = self._build_rtsp_url(config)
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                session.capture = cap
                session.config.is_online = True
                return {"status": "added", "camera_id": config.id, "online": True}
        except Exception as e:
            pass

        return {"status": "added", "camera_id": config.id, "online": False}

    async def remove_camera(self, camera_id: str) -> dict:
        if camera_id in self._capture_tasks:
            self._capture_tasks[camera_id].cancel()
            del self._capture_tasks[camera_id]

        session = self.cameras.pop(camera_id, None)
        if session and session.capture:
            session.capture.release()

        return {"status": "removed", "camera_id": camera_id}

    async def start_stream(self, camera_id: str, fps: int = 5, quality: int = 80) -> dict:
        session = self.cameras.get(camera_id)
        if not session:
            return {"status": "error", "message": "Camera not found"}

        if session.is_streaming:
            return {"status": "already_streaming", "camera_id": camera_id}

        if not session.capture:
            url = self._build_rtsp_url(session.config)
            session.capture = cv2.VideoCapture(url)

        if not session.capture or not session.capture.isOpened():
            return {"status": "error", "message": "Cannot connect to camera"}

        session.is_streaming = True
        session.fps = fps
        session.quality = quality
        session.config.is_online = True

        return {"status": "started", "camera_id": camera_id, "fps": fps}

    async def stop_stream(self, camera_id: str) -> dict:
        session = self.cameras.get(camera_id)
        if not session:
            return {"status": "error", "message": "Camera not found"}

        session.is_streaming = False
        if camera_id in self._capture_tasks:
            self._capture_tasks[camera_id].cancel()
            del self._capture_tasks[camera_id]

        return {"status": "stopped", "camera_id": camera_id}

    async def capture_frame(self, camera_id: str) -> Optional[str]:
        session = self.cameras.get(camera_id)
        if not session or not session.capture:
            return None

        try:
            ret, frame = session.capture.read()
            if not ret:
                session.config.is_online = False
                return None

            session.config.last_frame_time = time.time()
            session.config.is_online = True

            encode_params = [cv2.IMWRITE_JPEG_QUALITY, session.quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_params)
            return base64.b64encode(buffer).decode('utf-8')
        except Exception:
            return None

    def add_viewer(self, camera_id: str, viewer_id: str) -> int:
        session = self.cameras.get(camera_id)
        if session:
            session.viewers.add(viewer_id)
            return len(session.viewers)
        return 0

    def remove_viewer(self, camera_id: str, viewer_id: str) -> int:
        session = self.cameras.get(camera_id)
        if session:
            session.viewers.discard(viewer_id)
            return len(session.viewers)
        return 0

    def get_camera(self, camera_id: str) -> Optional[CameraSession]:
        return self.cameras.get(camera_id)

    def get_all_cameras(self) -> list[dict]:
        return [
            {
                "id": s.config.id,
                "name": s.config.name,
                "url": s.config.url,
                "type": s.config.type,
                "location": s.config.location,
                "is_online": s.config.is_online,
                "is_streaming": s.is_streaming,
                "viewer_count": len(s.viewers),
                "fps": s.fps,
            }
            for s in self.cameras.values()
        ]

    def get_online_cameras(self) -> list[dict]:
        return [c for c in self.get_all_cameras() if c["is_online"]]


rtsp_service = RTSPService()
