import asyncio
import base64
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import ollama
from app.services.rtsp_service import rtsp_service


class ObservationMode(str, Enum):
    IDLE = "idle"
    WATCH = "watch"
    SCAN = "scan"
    ALERT = "alert"


@dataclass
class ObservationConfig:
    camera_ids: list[str]
    mode: ObservationMode = ObservationMode.WATCH
    interval: float = 10.0
    alert_on_motion: bool = True
    alert_on_person: bool = True
    alert_on_unknown: bool = False
    track_people: bool = True
    describe_scene: bool = True
    custom_prompt: str = ""


@dataclass
class SceneObservation:
    camera_id: str
    camera_name: str
    timestamp: float
    description: str
    people_count: int
    people_actions: list[str]
    objects_detected: list[str]
    motion_detected: bool
    alerts: list[str]
    frame_b64: Optional[str] = None


@dataclass
class ObservationSession:
    id: str
    config: ObservationConfig
    is_active: bool = False
    last_observation: Optional[SceneObservation] = None
    observation_history: list[SceneObservation] = field(default_factory=list)
    task: Optional[asyncio.Task] = None


class VisionService:
    def __init__(self):
        self.sessions: dict[str, ObservationSession] = {}
        self._vision_model = "llava:7b"
        self._fallback_model = "llama3.2"
        self._on_observation: list[Callable] = []
        self._on_alert: list[Callable] = []

    def on_observation(self, callback: Callable):
        self._on_observation.append(callback)

    def on_alert(self, callback: Callable):
        self._on_alert.append(callback)

    async def analyze_frame(
        self,
        camera_id: str,
        prompt: str = None,
        context: str = None,
    ) -> dict:
        frame_b64 = await rtsp_service.capture_frame(camera_id)
        if not frame_b64:
            return {"status": "error", "message": "Cannot capture frame"}

        camera = rtsp_service.get_camera(camera_id)
        camera_name = camera.config.name if camera else camera_id

        if not prompt:
            prompt = (
                "Analyze this security camera feed. Describe in detail:\n"
                "1. How many people are visible and what they are doing\n"
                "2. Any unusual or suspicious activity\n"
                "3. Objects and their positions\n"
                "4. Overall scene description\n"
                "Be concise but thorough. Focus on activity and people."
            )

        if context:
            prompt = f"{context}\n\n{prompt}"

        try:
            response = ollama.chat(
                model=self._vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [frame_b64],
                    }
                ],
            )

            description = response["message"]["content"]
            parsed = self._parse_observation(description, camera_id, camera_name, frame_b64)

            return {
                "status": "success",
                "camera_id": camera_id,
                "camera_name": camera_name,
                "description": description,
                "people_count": parsed.people_count,
                "people_actions": parsed.people_actions,
                "objects_detected": parsed.objects_detected,
                "motion_detected": parsed.motion_detected,
                "alerts": parsed.alerts,
                "model": self._vision_model,
            }
        except Exception as e:
            return await self._fallback_analysis(camera_id, camera_name, frame_b64, prompt, str(e))

    async def _fallback_analysis(
        self,
        camera_id: str,
        camera_name: str,
        frame_b64: str,
        prompt: str,
        error: str,
    ) -> dict:
        try:
            response = ollama.chat(
                model=self._fallback_model,
                messages=[
                    {
                        "role": "user",
                        "content": f"[Vision analysis unavailable - model: {self._vision_model} error: {error}]\n\nUser asked: {prompt}\n\nRespond as J.A.R.V.I.S. explaining that vision analysis is temporarily unavailable but you can still help with other tasks.",
                    }
                ],
            )
            return {
                "status": "fallback",
                "camera_id": camera_id,
                "camera_name": camera_name,
                "description": response["message"]["content"],
                "people_count": 0,
                "people_actions": [],
                "objects_detected": [],
                "motion_detected": False,
                "alerts": [],
                "model": self._fallback_model,
            }
        except Exception as e2:
            return {"status": "error", "message": f"Both vision models failed: {error} | {e2}"}

    def _parse_observation(
        self,
        description: str,
        camera_id: str,
        camera_name: str,
        frame_b64: str,
    ) -> SceneObservation:
        description_lower = description.lower()

        people_count = 0
        if "no people" in description_lower or "no person" in description_lower:
            people_count = 0
        elif "one person" in description_lower or "a person" in description_lower or "1 person" in description_lower:
            people_count = 1
        elif "two people" in description_lower or "2 people" in description_lower:
            people_count = 2
        elif "three people" in description_lower or "3 people" in description_lower:
            people_count = 3
        elif "several people" in description_lower or "multiple people" in description_lower:
            people_count = 4
        elif "many people" in description_lower or "crowd" in description_lower:
            people_count = 5

        people_actions = []
        action_keywords = [
            "walking", "standing", "sitting", "running", "talking",
            "entering", "leaving", "opening", "closing", "carrying",
            "looking", "pointing", "gesturing", "waiting", "using phone",
        ]
        for action in action_keywords:
            if action in description_lower:
                people_actions.append(action)

        objects_detected = []
        object_keywords = [
            "car", "vehicle", "bike", "bicycle", "motorcycle",
            "dog", "cat", "animal",
            "package", "box", "bag",
            "door", "gate", "window",
            "umbrella", "luggage", "suitcase",
        ]
        for obj in object_keywords:
            if obj in description_lower:
                objects_detected.append(obj)

        motion_detected = any(w in description_lower for w in [
            "moving", "walking", "running", "approaching",
            "entering", "leaving", "driving", "passing by",
        ])

        alerts = []
        alert_keywords = [
            "suspicious", "unusual", "intruder", "unauthorized",
            "trespassing", "loitering", "breaking", "forced",
            "unknown person", "stranger", "unfamiliar",
        ]
        for keyword in alert_keywords:
            if keyword in description_lower:
                alerts.append(f"Alert: Detected '{keyword}' at {camera_name}")

        return SceneObservation(
            camera_id=camera_id,
            camera_name=camera_name,
            timestamp=time.time(),
            description=description,
            people_count=people_count,
            people_actions=people_actions,
            objects_detected=objects_detected,
            motion_detected=motion_detected,
            alerts=alerts,
            frame_b64=frame_b64,
        )

    async def start_observation(self, session_id: str, config: ObservationConfig) -> dict:
        if session_id in self.sessions and self.sessions[session_id].is_active:
            return {"status": "already_active", "session_id": session_id}

        session = ObservationSession(id=session_id, config=config)
        self.sessions[session_id] = session
        session.is_active = True
        session.task = asyncio.create_task(self._observation_loop(session))

        return {
            "status": "started",
            "session_id": session_id,
            "cameras": config.camera_ids,
            "mode": config.mode.value,
            "interval": config.interval,
        }

    async def stop_observation(self, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        session.is_active = False
        if session.task:
            session.task.cancel()
            try:
                await session.task
            except asyncio.CancelledError:
                pass

        return {"status": "stopped", "session_id": session_id}

    async def _observation_loop(self, session: ObservationSession):
        try:
            while session.is_active:
                for camera_id in session.config.camera_ids:
                    if not session.is_active:
                        break

                    camera = rtsp_service.get_camera(camera_id)
                    if not camera or not camera.config.is_online:
                        continue

                    result = await self.analyze_frame(
                        camera_id=camera_id,
                        prompt=self._build_observation_prompt(session.config),
                    )

                    if result["status"] in ["success", "fallback"]:
                        observation = SceneObservation(
                            camera_id=camera_id,
                            camera_name=result["camera_name"],
                            timestamp=time.time(),
                            description=result["description"],
                            people_count=result["people_count"],
                            people_actions=result["people_actions"],
                            objects_detected=result["objects_detected"],
                            motion_detected=result["motion_detected"],
                            alerts=result["alerts"],
                        )

                        session.last_observation = observation
                        session.observation_history.append(observation)

                        if len(session.observation_history) > 50:
                            session.observation_history = session.observation_history[-25:]

                        for callback in self._on_observation:
                            try:
                                await callback(observation)
                            except:
                                pass

                        if observation.alerts:
                            for callback in self._on_alert:
                                try:
                                    await callback(observation)
                                except:
                                    pass

                await asyncio.sleep(session.config.interval)

        except asyncio.CancelledError:
            pass

    def _build_observation_prompt(self, config: ObservationConfig) -> str:
        base_prompt = "Analyze this camera feed. "

        if config.mode == ObservationMode.WATCH:
            base_prompt += (
                "Watch and describe what you see. "
                "Focus on people, their actions, and any notable activity. "
                "Be concise but informative."
            )
        elif config.mode == ObservationMode.SCAN:
            base_prompt += (
                "Scan the entire scene systematically. "
                "List all visible people, objects, and describe the environment. "
                "Note any changes from a typical scene."
            )
        elif config.mode == ObservationMode.ALERT:
            base_prompt += (
                "Monitor for any suspicious, unusual, or security-relevant activity. "
                "Focus on: unknown people, loitering, unusual movements, "
                "potential threats, safety concerns. "
                "Only report if something notable is happening."
            )

        if config.track_people:
            base_prompt += " Count and track all visible people."

        if config.custom_prompt:
            base_prompt += f" {config.custom_prompt}"

        return base_prompt

    async def quick_look(self, camera_id: str) -> dict:
        return await self.analyze_frame(
            camera_id=camera_id,
            prompt=(
                "Quick look at this camera. "
                "Who is there? What are they doing? "
                "One short paragraph."
            ),
        )

    async def describe_for_command(self, camera_id: str, user_query: str) -> dict:
        return await self.analyze_frame(
            camera_id=camera_id,
            prompt=(
                f"A user is asking about this camera feed: '{user_query}'\n"
                "Analyze the camera and answer their question based on what you see. "
                "Be specific and helpful."
            ),
        )

    async def scan_all_cameras(self) -> list[dict]:
        results = []
        cameras = rtsp_service.get_online_cameras()

        for camera in cameras:
            result = await self.analyze_frame(
                camera_id=camera["id"],
                prompt=(
                    "Quick scan of this camera. "
                    "How many people? Any activity? "
                    "One sentence summary."
                ),
            )
            results.append(result)

        return results

    def get_session(self, session_id: str) -> Optional[ObservationSession]:
        return self.sessions.get(session_id)

    def get_all_sessions(self) -> list[dict]:
        return [
            {
                "id": s.id,
                "mode": s.config.mode.value,
                "cameras": s.config.camera_ids,
                "is_active": s.is_active,
                "interval": s.config.interval,
                "last_observation": {
                    "camera": s.last_observation.camera_name,
                    "description": s.last_observation.description,
                    "people_count": s.last_observation.people_count,
                    "timestamp": s.last_observation.timestamp,
                } if s.last_observation else None,
                "history_count": len(s.observation_history),
            }
            for s in self.sessions.values()
        ]

    def get_recent_observations(self, session_id: str, limit: int = 10) -> list[dict]:
        session = self.sessions.get(session_id)
        if not session:
            return []

        return [
            {
                "camera": o.camera_name,
                "description": o.description,
                "people_count": o.people_count,
                "people_actions": o.people_actions,
                "objects": o.objects_detected,
                "motion": o.motion_detected,
                "alerts": o.alerts,
                "timestamp": o.timestamp,
            }
            for o in session.observation_history[-limit:]
        ]


vision_service = VisionService()
