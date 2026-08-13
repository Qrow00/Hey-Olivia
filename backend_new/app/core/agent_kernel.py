"""AgentKernel - lifecycle and orchestration for J.A.R.V.I.S. V4.

Replaces V3's AppKernel: instead of fixed plugins, the agent composes
*skills* (registered intents) plus optional *services* (voice, vision,
memory, learner) gated by JARVIS_SERVICES.
"""

import asyncio
from typing import Any, Dict, List, Optional

from app.config import Config
from app.core.skill_registry import SkillRegistry


class AgentKernel:
    """Owns skill registry, optional services, and ordered startup/shutdown."""

    def __init__(self, cfg: Config, registry: Optional[SkillRegistry] = None):
        self.cfg = cfg
        self.registry = registry or SkillRegistry()
        self.services: Dict[str, Any] = {}
        self.startup_complete = False
        self.state_store = None

    # --- lifecycle ----------------------------------------------------------

    async def startup(self, state_store=None) -> None:
        self.state_store = state_store
        await self._start_services()
        self.startup_complete = True
        print(f"[Kernel] Started. Skills registered: {len(self.registry.names())}")

    async def shutdown(self) -> None:
        for name in reversed(list(self.services.keys())):
            svc = self.services[name]
            try:
                stop = getattr(svc, "stop", None)
                if stop is not None:
                    result = stop()
                    if asyncio.iscoroutine(result):
                        await result
            except Exception as e:
                print(f"[Kernel] Error stopping {name}: {e}")
        self.services.clear()
        self.startup_complete = False
        print("[Kernel] Shutdown complete")

    # --- services -----------------------------------------------------------

    async def _start_services(self) -> None:
        """Start optional services gated by JARVIS_SERVICES."""
        from app.memory.profile import ProfileStore
        from app.memory.episodic import EpisodicMemory
        from app.memory.vector_store import VectorStore

        profile = ProfileStore(self.state_store, self.cfg.profile)
        self.services["profile"] = profile

        if self.cfg.service_enabled("memory"):
            self.services["memory"] = EpisodicMemory(self.cfg.db_path)
            self.services["vectors"] = VectorStore(self.cfg.data_dir / "vectors.json")

        if self.cfg.service_enabled("voice"):
            from app.voice.wake_word import WakeWordEngine
            from app.voice.stt import SpeechToText
            from app.voice.tts import TextToSpeech
            self.services["wake_word"] = WakeWordEngine(self.cfg)
            self.services["stt"] = SpeechToText(self.cfg)
            self.services["tts"] = TextToSpeech(self.cfg)

        if self.cfg.service_enabled("vision"):
            from app.vision.face_db import FaceDB
            from app.vision.face_recognize import FaceRecognizer
            self.services["face_db"] = FaceDB(self.cfg)
            self.services["face_recognizer"] = FaceRecognizer(self.cfg)

        if self.cfg.service_enabled("learner"):
            from app.learner.feedback import FeedbackStore
            self.services["feedback"] = FeedbackStore(self.cfg.db_path)

        for name, svc in self.services.items():
            start = getattr(svc, "start", None)
            if start is not None:
                try:
                    result = start()
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    print(f"[Kernel] Service {name} start error: {e}")

    def get_service(self, name: str):
        return self.services.get(name)

    # --- intent dispatch ----------------------------------------------------

    async def execute_intent(self, intent: str, params: Dict[str, Any], ctx: Any = None) -> Dict[str, Any]:
        """Route an intent to a skill, broadcasting an event when possible."""
        result = await self.registry.execute(intent, params, ctx)
        if self.state_store is not None:
            try:
                await self.state_store.broadcast({
                    "type": "skill_event",
                    "handler": intent,
                    "success": result.get("success", False),
                })
            except Exception:
                pass
        return result
