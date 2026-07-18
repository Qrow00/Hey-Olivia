import uuid
import time
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class CaptureConfig:
    fps: int = 5
    quality: int = 80
    width: int = 720
    height: int = 1280
    format: str = "jpeg"


@dataclass
class ScreenAnalysis:
    enabled: bool = False
    interval: int = 5
    last_analysis: Optional[datetime] = None
    description: str = ""
    objects: list = field(default_factory=list)
    text: str = ""


@dataclass
class ScreenShareSession:
    id: str
    device_id: str
    source: str
    status: str
    started_at: datetime
    capture: CaptureConfig
    analysis: ScreenAnalysis
    viewer_count: int = 0
    last_frame_at: Optional[datetime] = None
    frame_count: int = 0


class ScreenShareService:
    def __init__(self):
        self.sessions: dict[str, ScreenShareSession] = {}
        self._viewers: dict[str, set] = {}

    def start_session(
        self,
        device_id: str,
        source: str = "pc",
        fps: int = 5,
        quality: int = 80,
        width: int = 720,
        height: int = 1280,
    ) -> ScreenShareSession:
        for sid, session in self.sessions.items():
            if session.device_id == device_id and session.status == "active":
                session.status = "inactive"

        session_id = str(uuid.uuid4())[:8]
        session = ScreenShareSession(
            id=session_id,
            device_id=device_id,
            source=source,
            status="starting",
            started_at=datetime.now(timezone.utc),
            capture=CaptureConfig(fps=fps, quality=quality, width=width, height=height),
            analysis=ScreenAnalysis(),
        )
        self.sessions[session_id] = session
        self._viewers[session_id] = set()
        return session

    def get_session(self, session_id: str) -> Optional[ScreenShareSession]:
        return self.sessions.get(session_id)

    def get_session_by_device(self, device_id: str) -> Optional[ScreenShareSession]:
        for session in self.sessions.values():
            if session.device_id == device_id and session.status in ("active", "starting"):
                return session
        return None

    def update_session_status(self, session_id: str, status: str):
        if session_id in self.sessions:
            self.sessions[session_id].status = status

    def record_frame(self, session_id: str):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_frame_at = datetime.now(timezone.utc)
            session.frame_count += 1
            if session.status == "starting":
                session.status = "active"

    def add_viewer(self, session_id: str, viewer_id: str) -> int:
        if session_id in self._viewers:
            self._viewers[session_id].add(viewer_id)
            self.sessions[session_id].viewer_count = len(self._viewers[session_id])
            return self.sessions[session_id].viewer_count
        return 0

    def remove_viewer(self, session_id: str, viewer_id: str) -> int:
        if session_id in self._viewers:
            self._viewers[session_id].discard(viewer_id)
            self.sessions[session_id].viewer_count = len(self._viewers[session_id])
            return self.sessions[session_id].viewer_count
        return 0

    def stop_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].status = "inactive"
            self._viewers.pop(session_id, None)

    def list_sessions(self) -> list:
        return [
            {
                "id": s.id,
                "device_id": s.device_id,
                "source": s.source,
                "status": s.status,
                "started_at": s.started_at.isoformat(),
                "capture": {
                    "fps": s.capture.fps,
                    "quality": s.capture.quality,
                    "width": s.capture.width,
                    "height": s.capture.height,
                    "format": s.capture.format,
                },
                "viewer_count": s.viewer_count,
                "frame_count": s.frame_count,
                "last_frame_at": (
                    s.last_frame_at.isoformat() if s.last_frame_at else None
                ),
            }
            for s in self.sessions.values()
        ]

    def cleanup_stale(self, timeout_seconds: int = 30):
        now = datetime.now(timezone.utc)
        for sid, session in list(self.sessions.items()):
            if session.status == "active" and session.last_frame_at:
                elapsed = (now - session.last_frame_at).total_seconds()
                if elapsed > timeout_seconds:
                    session.status = "inactive"


screen_share_service = ScreenShareService()
