"""Server-side voice session: openWakeWord wake detection + Silero VAD command capture."""
import asyncio
import base64
import re
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Awaitable, Callable, Optional

import numpy as np

FRAME_LENGTH = 1280          # samples per wake-model frame (80 ms @ 16kHz)
FRAME_BYTES = FRAME_LENGTH * 2
VAD_CHUNK_LENGTH = 480       # samples per VAD chunk (30 ms @ 16kHz)
VAD_CHUNK_BYTES = VAD_CHUNK_LENGTH * 2

WAKE_THRESHOLD = 0.5
VAD_THRESHOLD = 0.5
ONSET_FRAMES = 5             # ~150 ms
OFFSET_FRAMES = 30           # ~900 ms
MIN_COMMAND_SECONDS = 0.4
MAX_COMMAND_SECONDS = 12.0
SUPPRESSION_SECONDS = 1.0

_WAKE_PHRASE_PATTERNS = [
    re.compile(r"^\s*hey\s+jar[a-z]*", re.IGNORECASE),
    re.compile(r"^\s*jarvis", re.IGNORECASE),
]

_KEYWORD_MAP = {
    "hey jarvis": "hey_jarvis",
    "jarvis": "hey_jarvis",
    "alexa": "alexa",
    "hey mycroft": "hey_mycroft",
    "mycroft": "hey_mycroft",
    "hey rhasspy": "hey_rhasspy",
}


class SessionPhase(Enum):
    LISTENING = "listening"
    COMMAND = "command"
    THINKING = "thinking"
    SPEAKING = "speaking"


def strip_wake_phrase(text: str) -> str:
    cleaned = text.strip()
    for pattern in _WAKE_PHRASE_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            return cleaned[match.end():].strip(" .,!?")
    return cleaned


def _load_wake_model(model_names: list[str]):
    try:
        import openwakeword
        openwakeword.utils.download_models()
        from openwakeword.model import Model as OwwModel
        return OwwModel(wakeword_models=model_names, inference_framework="onnx")
    except Exception as e:
        print(f"[VOICE SESSION] Wake model load error: {e}")
        return None


def _load_vad():
    try:
        from openwakeword.vad import VAD
        return VAD(n_threads=1)
    except Exception as e:
        print(f"[VOICE SESSION] VAD load error: {e}")
        return None


async def _default_speech_to_text(audio: bytes) -> dict:
    from app.services.voice_service import voice_service
    return await voice_service.speech_to_text(audio)


async def _default_text_to_speech(text: str) -> bytes:
    from app.services.voice_profile_service import voice_profile_service
    from app.services.voice_service import voice_service
    profile = voice_profile_service.get_active_profile()
    return await voice_service.text_to_speech(
        text, voice=profile.voice, rate=profile.rate, pitch=profile.pitch
    )


async def _default_chat_completion(message: str, system_prompt: str) -> dict:
    from app.services.voice_service import voice_service
    return await voice_service.chat_completion(message=message, system_prompt=system_prompt)


def _default_parse_command(text: str) -> dict:
    from app.services.command_registry import command_registry
    return command_registry.parse_command(text)


async def _default_execute_command(text: str) -> dict:
    from app.services.command_registry import command_registry
    return await command_registry.execute_command(text)


def _default_get_profile(profile_id: str):
    from app.services.personality_service import personality_service
    return personality_service.get_profile(profile_id)


def _default_build_system_prompt(message: str, profile_id: str) -> str:
    from app.services.personality_service import personality_service
    return personality_service.get_system_prompt(profile_id)


class VoiceSession:
    def __init__(
        self,
        send: Callable[[dict], Awaitable[None]],
        *,
        profile_id: str = "default",
        threshold: float = WAKE_THRESHOLD,
        wake_factory: Optional[Callable[[list[str]], object]] = None,
        vad_factory: Optional[Callable[[], object]] = None,
        speech_to_text: Optional[Callable[[bytes], Awaitable[dict]]] = None,
        text_to_speech: Optional[Callable[[str], Awaitable[bytes]]] = None,
        chat_completion: Optional[Callable[[str, str], Awaitable[dict]]] = None,
        parse_command: Optional[Callable[[str], dict]] = None,
        execute_command: Optional[Callable[[str], Awaitable[dict]]] = None,
        get_profile: Optional[Callable[[str], object]] = None,
        build_system_prompt: Optional[Callable[[str, str], str]] = None,
        is_introduction: Optional[Callable[[], bool]] = None,
        on_intro_complete: Optional[Callable[[], None]] = None,
    ):
        self.phase = SessionPhase.LISTENING
        self._send = send
        self._profile_id = profile_id
        self._threshold = max(0.0, min(1.0, threshold))
        self._model_names = ["hey_jarvis"]

        self._wake_factory = wake_factory or _load_wake_model
        self._vad_factory = vad_factory or _load_vad
        self._speech_to_text = speech_to_text or _default_speech_to_text
        self._text_to_speech = text_to_speech or _default_text_to_speech
        self._chat_completion = chat_completion or _default_chat_completion
        self._parse_command = parse_command or _default_parse_command
        self._execute_command = execute_command or _default_execute_command
        self._get_profile = get_profile or _default_get_profile
        self._build_system_prompt = build_system_prompt or _default_build_system_prompt
        self._is_introduction = is_introduction or (lambda: False)
        self._on_intro_complete = on_intro_complete or (lambda: None)

        self._wake_model = None
        self._vad = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker: Optional[asyncio.Task] = None

        self._pcm_buffer = bytearray()
        self._vad_buffer = bytearray()
        self._command_buffer = bytearray()
        self._in_speech = False
        self._speech_frames = 0
        self._silence_frames = 0
        self._last_detection = 0.0

    # ── public API ─────────────────────────────────────────────────────────────────────
    async def start(self) -> dict:
        self._wake_model = await asyncio.to_thread(self._wake_factory, self._model_names)
        if self._wake_model is None:
            await self._send({"type": "voice_mode_ready", "status": "error",
                              "message": "Could not load openWakeWord model"})
            return {"status": "error", "message": "Could not load openWakeWord model"}
        self._vad = await asyncio.to_thread(self._vad_factory)
        if self._vad is None:
            await self._send({"type": "voice_mode_ready", "status": "error",
                              "message": "Could not load Silero VAD"})
            return {"status": "error", "message": "Could not load Silero VAD"}
        self.phase = SessionPhase.LISTENING
        self._worker = asyncio.create_task(self._run())
        await self._send({"type": "voice_mode_ready", "status": "ready"})
        await self._send({"type": "voice_phase", "phase": self.phase.value})
        return {"status": "success"}

    async def feed_pcm(self, audio_b64: str):
        data = base64.b64decode(audio_b64)
        self._queue.put_nowait(data)

    async def on_tts_done(self):
        if self.phase == SessionPhase.SPEAKING:
            self.phase = SessionPhase.LISTENING
            self._reset_command_buffers()
            await self._send({"type": "voice_phase", "phase": self.phase.value})

    async def stop(self):
        self._queue.put_nowait(None)
        if self._worker is not None:
            try:
                await asyncio.wait_for(self._worker, timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._worker.cancel()
            self._worker = None
        self._wake_model = None
        self._vad = None
        self.phase = SessionPhase.LISTENING

    def set_threshold(self, value: float):
        self._threshold = max(0.0, min(1.0, float(value)))

    def set_keywords(self, keywords: list):
        self._model_names = []
        for kw in keywords:
            kw_lower = kw.lower().strip()
            mapped = _KEYWORD_MAP.get(kw_lower, kw_lower.replace(" ", "_"))
            if mapped not in self._model_names:
                self._model_names.append(mapped)

    def get_config(self) -> dict:
        return {
            "models": list(self._model_names),
            "threshold": self._threshold,
            "engine": "openWakeWord",
        }

    # ── internals ──────────────────────────────────────────────────────────────────────
    async def _run(self):
        while True:
            data = await self._queue.get()
            if data is None:
                break
            try:
                await self._process_audio(data)
            except Exception as e:
                import traceback
                traceback.print_exc()
                await self._emit_error(f"{type(e).__name__}: {e}")

    async def _process_audio(self, data: bytes):
        self._pcm_buffer.extend(data)
        while len(self._pcm_buffer) >= FRAME_BYTES:
            frame = bytes(self._pcm_buffer[:FRAME_BYTES])
            del self._pcm_buffer[:FRAME_BYTES]
            await self._handle_frame(frame)

    async def _handle_frame(self, frame: bytes):
        if self.phase in (SessionPhase.LISTENING, SessionPhase.SPEAKING):
            await self._wake_scan(frame)
        elif self.phase == SessionPhase.COMMAND:
            await self._vad_scan(frame)

    async def _wake_scan(self, frame: bytes):
        audio = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32768.0
        scores = self._wake_model.predict(audio)
        score = max(float(scores.get(m, 0.0)) for m in self._model_names)
        if score <= self._threshold:
            return
        now = time.monotonic()
        if now - self._last_detection < SUPPRESSION_SECONDS:
            return
        self._last_detection = now
        self._wake_model.reset()
        self._reset_command_buffers()
        self.phase = SessionPhase.COMMAND
        await self._send({
            "type": "wake_word_detected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await self._send({"type": "voice_phase", "phase": self.phase.value})

    async def _vad_scan(self, frame: bytes):
        pass  # Task 3

    async def _track_vad(self, prob: float, chunk: bytes):
        pass  # Task 3

    async def _finalize(self):
        pass  # Task 4

    async def _emit_error(self, message: str):
        self.phase = SessionPhase.LISTENING
        await self._send({"type": "voice_error", "message": message})
        await self._send({"type": "voice_phase", "phase": self.phase.value})

    def _reset_command_buffers(self):
        self._command_buffer.clear()
        self._vad_buffer.clear()
        self._in_speech = False
        self._speech_frames = 0
        self._silence_frames = 0
