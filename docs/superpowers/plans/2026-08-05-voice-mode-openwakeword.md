# Voice Mode Rebuild Around openWakeWord — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild JARVIS voice mode as a server-driven streaming loop where openWakeWord runs frame-by-frame (with Silero VAD command capture and barge-in) inside a per-connection `VoiceSession`, and the Flutter client becomes a thin PCM streaming pump.

**Architecture:** The client streams 16kHz mono s16 PCM continuously over WebSocket (`audio_frame`). The backend runs one `VoiceSession` per connection with a phase state machine (LISTENING → COMMAND → THINKING → SPEAKING). LISTENING runs openWakeWord `hey_jarvis` frame-by-frame (1280 samples/80ms); detection enters COMMAND. COMMAND runs the bundled Silero VAD (via `openwakeword.vad.VAD`, no new dependency) on 480-sample chunks with onset/offset endpointing; end-of-speech triggers STT → command registry/LLM → TTS → `voice_response` and SPEAKING. During SPEAKING the wake model stays active so re-detection barge-in interrupts playback. The spec is `docs/superpowers/specs/2026-08-05-voice-mode-openwakeword-design.md`; this plan implements it exactly.

**Tech Stack:** Python 3.14 (FastAPI + `openwakeword`, `openwakeword.vad`, `numpy`), pytest (async tests use `@pytest.mark.anyio`, matching the existing suite — do NOT add pytest-asyncio), Flutter/Dart 3 client (ffmpeg on Windows, MethodChannel MicRecorder on Android).

## Global Constraints

(Every task's requirements implicitly include all of these. Values copied verbatim from the spec.)

- **No new Python dependencies.** `openwakeword` is already installed; `silero_vad.onnx` is bundled in `backend\.venv\Lib\site-packages\openwakeword\resources\models\`. Use `openwakeword.vad.VAD` (model_path defaults to the bundled file).
- **Per-session model instances.** openWakeWord keeps rolling state (`prediction_buffer`), so never share one `Model`/`VAD` across connections. Each `VoiceSession` owns its own, loaded lazily via `asyncio.to_thread`.
- **Frame sizes:** wake-model frame = 1280 samples (80ms @ 16kHz) = 2560 bytes of s16 PCM; VAD chunk = 480 samples (30ms) = 960 bytes.
- **Endpointing:** onset = 5 consecutive VAD probabilities > 0.5 (~150ms); offset = 30 consecutive < 0.5 (~900ms); min command 0.4s; max 12s (force-finalize). Detection threshold default 0.5 (from `voice.wake_word_sensitivity`).
- **Suppression:** ignore wake detections for 1.0s after any detection (`_last_detection` guard).
- **Wake word required every turn.** No follow-up window. `tts_done` → SPEAKING → LISTENING only.
- **Protocol** (client→server): `voice_mode_start {sample_rate: 16000}`, `audio_frame {audio: base64(pcm)}`, `tts_done {}`, `voice_mode_stop {}`, `wake_word_config {setting, value}` (kept). (server→client): `voice_mode_ready {status}`, `voice_phase {phase}`, `wake_word_detected {timestamp}`, `avatar_state {state}`, `voice_response {transcription, response, audio, model, ...}`, `voice_error {message}`. Removed: `voice_chunk`, `wake_word_miss`, `wake_word_error`.
- **Client phase enum:** `VoicePhase { idle, listening, command, thinking, speaking }`, updated from `voice_phase`. Keep `isListening` and `voicePhase` getters.
- **Barge-in:** the mic is NEVER paused during playback. On `wake_word_detected` while a player is active, stop the player; do not send `tts_done` for an interrupted play.
- **Non-goals:** on-device Android detection, multi-turn follow-up, PTT (`push_to_talk` untouched).
- **Tests:** run from `backend\` via `.\.venv\Scripts\python.exe -m pytest`. Async tests use `@pytest.mark.anyio` (anyio is already installed; existing `tests/test_api.py` uses it). Existing `test_commands.py` / `test_api.py` must stay green. Use injected fake detectors (no real model) for determinism; one real-model smoke test skips when `openwakeword` is missing.
- **Client verify:** `flutter analyze` run from `client\` must be clean.
- **Git:** the working tree contains unrelated pre-existing changes. Only `git add` the exact files listed in each task. Commit style is Conventional Commits (`feat:`, `refactor:`, `docs:`, `test:`).
- **Backend runtime:** never run the backend inside the opencode shell; the plan's tasks only run pytest and import checks.

## File Structure

**Create**
- `backend/app/services/voice_session_service.py` — `SessionPhase` enum, `strip_wake_phrase`, frame constants, `VoiceSession` state machine (wake scan, VAD scan, finalize, worker). One responsibility: the whole server voice loop.
- `backend/tests/test_voice_session.py` — unit tests with fake send/detectors/LLM deps + one real-model smoke test.

**Modify**
- `backend/app/routers/websocket.py` — new `voice_mode_start`/`audio_frame`/`tts_done`/`voice_mode_stop` handlers, `voice_sessions` registry, dispatch branches, disconnect teardown, re-point `wake_word_config`; then remove `handle_voice_chunk`, `_process_voice_command`, `client_voice_state`, `wake_word_service` usage, `_WAKE_PHRASE_PATTERNS`/`_strip_wake_phrase`.
- `client/lib/services/voice_service.dart` — streaming frame pump replaces energy VAD; new message handling; barge-in playback.
- `client/lib/screens/home_screen.dart` — phase-driven UI, status text, auto-start gated on `wake_word_enabled`.
- `vault/API_DOCS.md`, `vault/Voice Pipeline.md`, `vault/AGENTS.md`, `vault/memory/Decisions/openWakeWord over Whisper for wake word.md` — doc updates.

**Delete**
- `backend/app/services/wake_word_service.py` (replaced by `VoiceSession`).

---

## Task 1: VoiceSession skeleton — phases, buffers, worker, start/stop

**Files:**
- Create: `backend/app/services/voice_session_service.py`
- Test: `backend/tests/test_voice_session.py`

**Interfaces:**
- Consumes: `safe_send(websocket, payload)` pattern from `websocket.py` (wired later in Task 6); no module imports at load time except `numpy`, `asyncio`, `base64`, `re`, `time`, `enum` — all heavy services (`voice_service`, `command_registry`, `personality_service`, `voice_profile_service`) are imported lazily inside `_default_*` functions.
- Produces: `SessionPhase(Enum)`, `strip_wake_phrase(text: str) -> str`, constants `FRAME_LENGTH`, `FRAME_BYTES`, `VAD_CHUNK_LENGTH`, `VAD_CHUNK_BYTES`, `WAKE_THRESHOLD`, `VAD_THRESHOLD`, `ONSET_FRAMES`, `OFFSET_FRAMES`, `MIN_COMMAND_SECONDS`, `MAX_COMMAND_SECONDS`, `SUPPRESSION_SECONDS`, `_load_wake_model(model_names: list[str]) -> object | None`, `_load_vad() -> object | None`, and `class VoiceSession` with constructor:

```python
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
) -> None
```

Public async API: `start() -> dict`, `feed_pcm(audio_b64: str)`, `on_tts_done()`, `stop()`. Sync: `set_threshold(value: float)`, `set_keywords(keywords: list)`, `get_config() -> dict`. Public attributes: `phase: SessionPhase`. Internal (used by later tasks and tests): `_process_audio(data: bytes)`, `_handle_frame(frame: bytes)`, `_wake_scan(frame: bytes)`, `_vad_scan(frame: bytes)`, `_track_vad(prob: float, chunk: bytes)`, `_finalize()`, `_reset_command_buffers()`, `_emit_error(message: str)`, `_send(payload)`.

> Engineering note: `VoiceSession` takes an async `send(payload)` callable instead of a raw `websocket` object so the state machine is unit-testable without a live socket. The WS handler wires `send=lambda payload: safe_send(websocket, payload)` (Task 6).

- [ ] **Step 1: Write the failing tests**

```python
import asyncio
import base64
import time

import numpy as np
import pytest

from app.services.voice_session_service import (
    VoiceSession,
    SessionPhase,
    strip_wake_phrase,
    FRAME_BYTES,
    VAD_CHUNK_BYTES,
)


class SendCollector:
    def __init__(self):
        self.messages = []

    async def __call__(self, payload: dict):
        self.messages.append(payload)


class FakeWakeModel:
    def __init__(self, score=0.0):
        self.score = score
        self.reset_calls = 0
        self.frames = []

    def predict(self, audio):
        self.frames.append(audio.copy())
        return {"hey_jarvis": self.score}

    def reset(self):
        self.reset_calls += 1


class FakeVad:
    def __init__(self, probs):
        self.probs = list(probs)
        self.index = 0
        self.chunks = []

    def predict(self, chunk):
        self.chunks.append(chunk.copy())
        p = self.probs[min(self.index, len(self.probs) - 1)]
        self.index += 1
        return float(p)


class FakeProfile:
    def __init__(self):
        self.preferred_name = "Boss"
        self.introduced = False
        self.saved = False

    def _save(self):
        self.saved = True


SILENT_FRAME = bytes(FRAME_BYTES)  # 2560 zero bytes = 1280 int16 samples


def make_session(send, **kw):
    kw.setdefault("wake_factory", lambda names: FakeWakeModel())
    kw.setdefault("vad_factory", lambda: FakeVad([0.1]))
    return VoiceSession(send, **kw)


@pytest.mark.anyio
async def test_start_ready():
    send = SendCollector()
    session = make_session(send)
    result = await session.start()
    assert result["status"] == "success"
    assert any(m["type"] == "voice_mode_ready" and m["status"] == "ready" for m in send.messages)
    assert session.phase == SessionPhase.LISTENING
    await session.stop()


@pytest.mark.anyio
async def test_start_engine_load_failure():
    send = SendCollector()
    session = VoiceSession(send, wake_factory=lambda names: None, vad_factory=lambda: FakeVad([0.1]))
    result = await session.start()
    assert result["status"] == "error"
    ready = [m for m in send.messages if m["type"] == "voice_mode_ready"]
    assert ready and ready[-1]["status"] == "error"
    assert session._worker is None


@pytest.mark.anyio
async def test_tts_done_returns_to_listening():
    send = SendCollector()
    session = make_session(send)
    session.phase = SessionPhase.SPEAKING
    await session.on_tts_done()
    assert session.phase == SessionPhase.LISTENING
    assert any(m["type"] == "voice_phase" and m["phase"] == "listening" for m in send.messages)


@pytest.mark.anyio
async def test_stop_cleans_up():
    send = SendCollector()
    session = make_session(send)
    await session.start()
    await session.stop()
    assert session._wake_model is None
    assert session._vad is None
    assert session._worker is None


def test_set_threshold_clamped():
    s = VoiceSession(SendCollector())
    s.set_threshold(1.7)
    assert s._threshold == 1.0
    s.set_threshold(-0.2)
    assert s._threshold == 0.0


def test_strip_wake_phrase():
    assert strip_wake_phrase("hey jarvis turn on the lights") == "turn on the lights"
    assert strip_wake_phrase("jarvis, what time is it") == "what time is it"
    assert strip_wake_phrase("no wake word here") == "no wake word here"


@pytest.mark.anyio
async def test_feed_pcm_puts_decoded_bytes_on_queue():
    session = VoiceSession(SendCollector())
    encoded = base64.b64encode(b"\x00\x01\x02\x03").decode()
    await session.feed_pcm(encoded)
    item = session._queue.get_nowait()
    assert item == b"\x00\x01\x02\x03"
```

- [ ] **Step 2: Run test to verify it fails**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.voice_session_service'`

- [ ] **Step 3: Write the minimal implementation**

Create `backend/app/services/voice_session_service.py`:

```python
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

    # ── public API ───────────────────────────────────────────────────
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

    # ── internals ────────────────────────────────────────────────────
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
        pass  # Task 2

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
```

- [ ] **Step 4: Run test to verify it passes**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -v`
Expected: PASS (all tests in this file)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/voice_session_service.py backend/tests/test_voice_session.py
git commit -m "feat: voice session skeleton with streaming frame pump"
```

---

## Task 2: Wake detection — LISTENING/SPEAKING scan, suppression, barge-in

**Files:**
- Modify: `backend/app/services/voice_session_service.py` (implement `_wake_scan`)
- Test: `backend/tests/test_voice_session.py`

**Interfaces:**
- Consumes: `VoiceSession` from Task 1 (`phase`, `_wake_model.predict(frame_float32) -> dict`, `_model_names`, `_threshold`, `_last_detection`, `_send`, `_reset_command_buffers`, `SessionPhase`).
- Produces: `wake_word_detected {timestamp}` (ISO-8601 UTC) + `voice_phase {phase: "command"}` on detection; `_last_detection = time.monotonic()`; wake model reset via `self._wake_model.reset()`; applies the 1.0s suppression guard; barge-in from SPEAKING (same code path — LISTENING and SPEAKING both wake-scan).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_voice_session.py`:

```python
@pytest.mark.anyio
async def test_wake_detection_transitions_to_command():
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.9)
    await session._process_audio(SILENT_FRAME)
    assert any(m["type"] == "wake_word_detected" for m in send.messages)
    assert session.phase == SessionPhase.COMMAND
    phases = [m["phase"] for m in send.messages if m["type"] == "voice_phase"]
    assert phases == ["command"]


@pytest.mark.anyio
async def test_no_detection_below_threshold():
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.1)
    await session._process_audio(SILENT_FRAME)
    assert not any(m["type"] == "wake_word_detected" for m in send.messages)
    assert session.phase == SessionPhase.LISTENING


@pytest.mark.anyio
async def test_detection_suppressed_within_one_second():
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.9)
    session._last_detection = time.monotonic()
    await session._process_audio(SILENT_FRAME)
    assert not any(m["type"] == "wake_word_detected" for m in send.messages)


@pytest.mark.anyio
async def test_detection_during_speaking_barge_in():
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.9)
    session.phase = SessionPhase.SPEAKING
    await session._process_audio(SILENT_FRAME)
    assert session.phase == SessionPhase.COMMAND
    assert any(m["type"] == "wake_word_detected" for m in send.messages)


@pytest.mark.anyio
async def test_wake_model_reset_after_detection():
    send = SendCollector()
    session = VoiceSession(send)
    model = FakeWakeModel(score=0.9)
    session._wake_model = model
    await session._process_audio(SILENT_FRAME)
    assert model.reset_calls == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -k "detection or suppressed or reset" -v`
Expected: FAIL — no `wake_word_detected` message is ever sent (`_wake_scan` is a stub)

- [ ] **Step 3: Write the minimal implementation**

Replace the `_wake_scan` stub in `voice_session_service.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -k "detection or suppressed or reset" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/voice_session_service.py backend/tests/test_voice_session.py
git commit -m "feat: wake word detection with suppression and barge-in"
```

---

## Task 3: Silero VAD command endpointing

**Files:**
- Modify: `backend/app/services/voice_session_service.py` (implement `_vad_scan`, `_track_vad`)
- Test: `backend/tests/test_voice_session.py`

**Interfaces:**
- Consumes: `_vad.predict(np.int16 chunk) -> float` (verified: returns a scalar average over the chunk — maintain per-session state via the same VAD object across calls), `SessionPhase`, `_command_buffer`, `_vad_buffer`, `_in_speech`, `_speech_frames`, `_silence_frames`, `_finalize()` (Task 4).
- Produces: on end-of-speech (or max-duration) with buffer ≥ 0.4s → calls `await self._finalize()`; with buffer < 0.4s → resets buffers and returns to LISTENING (sends `voice_phase {phase: "listening"}`).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_voice_session.py`:

```python
@pytest.mark.anyio
async def test_vad_endpointing_finalizes_command():
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.0)
    session._vad = FakeVad([0.9] * 60 + [0.1] * 40)
    session.phase = SessionPhase.COMMAND
    await session._process_audio(SILENT_FRAME * 50)
    responses = [m for m in send.messages if m["type"] == "voice_response"]
    assert len(responses) == 1
    assert session.phase == SessionPhase.SPEAKING
    phases = [m["phase"] for m in send.messages if m["type"] == "voice_phase"]
    assert "thinking" in phases and "speaking" in phases


@pytest.mark.anyio
async def test_vad_short_command_is_discarded():
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.0)
    session._vad = FakeVad([0.9] * 5 + [0.1] * 40)
    session.phase = SessionPhase.COMMAND
    await session._process_audio(SILENT_FRAME * 25)
    assert not any(m["type"] == "voice_response" for m in send.messages)
    assert session.phase == SessionPhase.LISTENING
    last_phase = [m["phase"] for m in send.messages if m["type"] == "voice_phase"][-1]
    assert last_phase == "listening"


@pytest.mark.anyio
async def test_vad_max_duration_force_finalize():
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.0)
    session._vad = FakeVad([0.9] * 1000)
    session.phase = SessionPhase.COMMAND
    await session._process_audio(SILENT_FRAME * 205)
    assert any(m["type"] == "voice_response" for m in send.messages)
    assert session.phase == SessionPhase.SPEAKING
```

- [ ] **Step 2: Run test to verify it fails**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -k "vad_" -v`
Expected: FAIL — `_vad_scan` is a stub; no `voice_response` ever appears

- [ ] **Step 3: Write the minimal implementation**

Replace the `_vad_scan` and `_track_vad` stubs in `voice_session_service.py`:

```python
    async def _vad_scan(self, frame: bytes):
        self._vad_buffer.extend(frame)
        while len(self._vad_buffer) >= VAD_CHUNK_BYTES:
            chunk = bytes(self._vad_buffer[:VAD_CHUNK_BYTES])
            del self._vad_buffer[:VAD_CHUNK_BYTES]
            prob = float(self._vad.predict(np.frombuffer(chunk, dtype=np.int16)))
            await self._track_vad(prob, chunk)

    async def _track_vad(self, prob: float, chunk: bytes):
        if prob > VAD_THRESHOLD:
            self._silence_frames = 0
            if not self._in_speech:
                self._speech_frames += 1
                if self._speech_frames >= ONSET_FRAMES:
                    self._in_speech = True
                    self._speech_frames = 0
        else:
            self._speech_frames = 0
            if self._in_speech:
                self._silence_frames += 1
                if self._silence_frames >= OFFSET_FRAMES:
                    await self._finalize()
                    return
            else:
                self._silence_frames = 0
            return
        if self._in_speech:
            self._command_buffer.extend(chunk)
            if len(self._command_buffer) // 2 >= MAX_COMMAND_SECONDS * 16000:
                await self._finalize()
```

- [ ] **Step 4: Run test to verify it passes**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -k "vad_" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/voice_session_service.py backend/tests/test_voice_session.py
git commit -m "feat: Silero VAD command endpointing"
```

---

## Task 4: Finalize path — commands, LLM, introduction, error handling

**Files:**
- Modify: `backend/app/services/voice_session_service.py` (implement `_finalize`, `_finalize_introduction`, `_finalize_command`)
- Test: `backend/tests/test_voice_session.py`

**Interfaces:**
- Consumes: injected `_speech_to_text(audio) -> dict{text, confidence}`, `_text_to_speech(text) -> bytes`, `_chat_completion(message, system_prompt) -> dict{response, model}`, `_parse_command(text) -> dict{matched, handler}`, `_execute_command(text) -> dict{result}`, `_get_profile(profile_id) -> ProfileData-like (preferred_name, introduced, _save)`, `_build_system_prompt(message, profile_id) -> str`, `_is_introduction() -> bool`, `_on_intro_complete()`, `_emit_error`.
- Produces the server→client messages specified in Global Constraints. `voice_response` payload shape: `{"type", "transcription", "confidence", "response", "audio" (base64), "model"}` plus optional `is_introduction`/`is_farewell`/`exit_app`. Farewell text: `f"Goodbye, {profile.preferred_name}. It was a pleasure assisting you."`; introduction replies exactly:
  - with a name: `f"Nice to meet you, {name}! How may I assist you today?"`
  - without: `"No problem! I will call you Boss. How may I assist you today?"`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_voice_session.py`:

```python
def finalize_session(send, **kw):
    defaults = dict(
        speech_to_text=lambda audio: {"text": "turn on the lights", "confidence": 0.9},
        text_to_speech=lambda text: b"MP3DATA",
        chat_completion=lambda msg, sp: {"response": "Done.", "model": "llama3.2"},
        parse_command=lambda text: {"matched": True, "handler": "lights", "category": "smart_home"},
        execute_command=lambda text: {"result": {"status": "success", "message": "Lights on"}},
        get_profile=lambda pid: FakeProfile(),
    )
    defaults.update(kw)
    return VoiceSession(send, **defaults)


async def run_finalize(session, seconds=3.0):
    session.phase = SessionPhase.COMMAND
    session._command_buffer = bytearray(b"\x00\x00" * int(seconds * 16000))
    await session._finalize()


@pytest.mark.anyio
async def test_finalize_matched_command():
    send = SendCollector()
    session = finalize_session(send)
    await run_finalize(session)
    resp = [m for m in send.messages if m["type"] == "voice_response"][-1]
    assert resp["response"] == "Done."
    assert resp["model"] == "llama3.2"
    assert resp["audio"] is not None
    assert session.phase == SessionPhase.SPEAKING


@pytest.mark.anyio
async def test_finalize_llm_only_when_no_command_match():
    send = SendCollector()
    session = finalize_session(send, parse_command=lambda text: {"matched": False})
    await run_finalize(session)
    resp = [m for m in send.messages if m["type"] == "voice_response"][-1]
    assert resp["response"] == "Done."
    assert resp["transcription"] == "turn on the lights"


@pytest.mark.anyio
async def test_finalize_goodbye():
    send = SendCollector()
    session = finalize_session(
        send,
        parse_command=lambda text: {"matched": True, "handler": "goodbye"},
    )
    await run_finalize(session)
    resp = [m for m in send.messages if m["type"] == "voice_response"][-1]
    assert resp["is_farewell"] is True
    assert resp["exit_app"] is True
    assert "Goodbye, Boss." in resp["response"]


@pytest.mark.anyio
async def test_finalize_empty_transcription_returns_to_listening():
    send = SendCollector()
    session = finalize_session(send, speech_to_text=lambda audio: {"text": "", "confidence": 0.0})
    await run_finalize(session)
    assert not any(m["type"] == "voice_response" for m in send.messages)
    assert session.phase == SessionPhase.LISTENING


@pytest.mark.anyio
async def test_finalize_strip_wake_phrase_from_transcription():
    send = SendCollector()
    session = finalize_session(send, speech_to_text=lambda audio: {"text": "hey jarvis set alarm", "confidence": 0.9})
    await run_finalize(session)
    resp = [m for m in send.messages if m["type"] == "voice_response"][-1]
    assert resp["transcription"] == "set alarm"


@pytest.mark.anyio
async def test_introduction_captures_name():
    send = SendCollector()
    profile = FakeProfile()
    session = finalize_session(
        send,
        get_profile=lambda pid: profile,
        is_introduction=lambda: True,
    )
    await run_finalize(session)
    assert profile.preferred_name == "Alice Smith"
    assert profile.introduced is True
    assert profile.saved is True
    resp = [m for m in send.messages if m["type"] == "voice_response"][-1]
    assert resp["model"] == "introduction"
    assert resp["is_introduction"] is True
    assert "Alice Smith" in resp["response"]
    assert session.phase == SessionPhase.SPEAKING


@pytest.mark.anyio
async def test_introduction_fallback_boss():
    send = SendCollector()
    profile = FakeProfile()
    session = finalize_session(
        send,
        get_profile=lambda pid: profile,
        is_introduction=lambda: True,
        speech_to_text=lambda audio: {"text": "", "confidence": 0.0},
    )
    await run_finalize(session)
    assert profile.preferred_name == "Boss"
    assert profile.introduced is True


@pytest.mark.anyio
async def test_finalize_error_sends_voice_error():
    send = SendCollector()
    session = finalize_session(
        send,
        speech_to_text=lambda audio: (_ for _ in ()).throw(RuntimeError("stt failed")),
    )
    await run_finalize(session)
    errors = [m for m in send.messages if m["type"] == "voice_error"]
    assert errors and "stt failed" in errors[-1]["message"]
    assert session.phase == SessionPhase.LISTENING


@pytest.mark.anyio
async def test_intro_complete_callback_invoked():
    send = SendCollector()
    calls = []
    session = finalize_session(
        send,
        is_introduction=lambda: True,
        on_intro_complete=lambda: calls.append(True),
    )
    await run_finalize(session)
    assert calls == [True]
```

- [ ] **Step 2: Run test to verify it fails**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -k "finalize or introduction or goodbye or intro_complete" -v`
Expected: FAIL — `_finalize` is a stub

- [ ] **Step 3: Write the minimal implementation**

Replace the `_finalize` stub in `voice_session_service.py` with `_finalize`, `_finalize_introduction`, and `_finalize_command`:

```python
    async def _finalize(self):
        duration = len(self._command_buffer) / 2 / 16000
        if duration < MIN_COMMAND_SECONDS:
            self._reset_command_buffers()
            self.phase = SessionPhase.LISTENING
            await self._send({"type": "voice_phase", "phase": self.phase.value})
            return
        audio = bytes(self._command_buffer)
        self._reset_command_buffers()
        self.phase = SessionPhase.THINKING
        await self._send({"type": "voice_phase", "phase": self.phase.value})
        await self._send({"type": "avatar_state", "state": "thinking"})
        try:
            if self._is_introduction():
                await self._finalize_introduction(audio)
            else:
                await self._finalize_command(audio)
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self._emit_error(f"{type(e).__name__}: {e}")

    async def _finalize_introduction(self, audio: bytes):
        profile = self._get_profile(self._profile_id)
        stt = await self._speech_to_text(audio)
        text = stt.get("text", "").strip().strip(".").strip()
        name = " ".join(w.capitalize() for w in text.split() if w.isalpha())
        if name:
            profile.preferred_name = name
            response_text = f"Nice to meet you, {name}! How may I assist you today?"
        else:
            profile.preferred_name = "Boss"
            response_text = "No problem! I will call you Boss. How may I assist you today?"
        profile.introduced = True
        profile._save()
        self._on_intro_complete()
        tts = await self._text_to_speech(response_text)
        await self._send({"type": "avatar_state", "state": "speaking"})
        await self._send({
            "type": "voice_response",
            "transcription": text,
            "response": response_text,
            "audio": base64.b64encode(tts).decode(),
            "model": "introduction",
            "is_introduction": True,
        })
        self.phase = SessionPhase.SPEAKING
        await self._send({"type": "voice_phase", "phase": self.phase.value})

    async def _finalize_command(self, audio: bytes):
        stt = await self._speech_to_text(audio)
        text = stt.get("text", "").strip()
        command_text = strip_wake_phrase(text)
        if not command_text:
            self.phase = SessionPhase.LISTENING
            await self._send({"type": "voice_phase", "phase": self.phase.value})
            return
        profile = self._get_profile(self._profile_id)
        result = self._parse_command(command_text)
        if result.get("matched"):
            if result.get("handler") == "goodbye":
                farewell_text = f"Goodbye, {profile.preferred_name}. It was a pleasure assisting you."
                tts = await self._text_to_speech(farewell_text)
                await self._send({"type": "avatar_state", "state": "speaking"})
                await self._send({
                    "type": "voice_response",
                    "transcription": command_text,
                    "response": farewell_text,
                    "audio": base64.b64encode(tts).decode(),
                    "model": "farewell",
                    "is_farewell": True,
                    "exit_app": True,
                })
                self.phase = SessionPhase.SPEAKING
                await self._send({"type": "voice_phase", "phase": self.phase.value})
                return
            execution = await self._execute_command(command_text)
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
                        extra_info += f"\n{k}: {v}"
            prompt = (
                f'The user said: "{command_text}"\n'
                f"Command result: {result_message}{extra_info}\n\n"
                "Respond with a short natural sentence (1-2 lines) about what was done. Be helpful and conversational."
            )
        else:
            prompt = command_text
        llm = await self._chat_completion(
            prompt,
            self._build_system_prompt(command_text, self._profile_id),
        )
        response_text = llm["response"]
        tts = await self._text_to_speech(response_text)
        await self._send({"type": "avatar_state", "state": "speaking"})
        await self._send({
            "type": "voice_response",
            "transcription": command_text,
            "confidence": stt.get("confidence", 0.0),
            "response": response_text,
            "audio": base64.b64encode(tts).decode(),
            "model": llm.get("model", "llama3.2"),
        })
        self.phase = SessionPhase.SPEAKING
        await self._send({"type": "voice_phase", "phase": self.phase.value})
```

- [ ] **Step 4: Run test to verify it passes**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py -v`
Expected: PASS (Tasks 1–4 tests all green)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/voice_session_service.py backend/tests/test_voice_session.py
git commit -m "feat: voice session finalize path (commands, LLM, introduction)"
```

---

## Task 5: Real-model smoke test

**Files:**
- Test: `backend/tests/test_voice_session.py`

**Interfaces:**
- Consumes: `_load_wake_model`, `_load_vad` from Task 1 (real openwakeword). Verified in this repo: `openwakeword.vad.VAD.predict(x, frame_size=480)` accepts `np.int16` and returns a scalar probability; `Model.predict(x)` accepts `float32` normalized audio and returns a dict keyed by model name.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_voice_session.py`:

```python
def test_real_wake_model_and_vad_load():
    pytest.importorskip("openwakeword")
    from app.services.voice_session_service import _load_wake_model, _load_vad

    model = _load_wake_model(["hey_jarvis"])
    assert model is not None
    vad = _load_vad()
    assert vad is not None

    frame = np.zeros(1280, dtype=np.int16)
    scores = model.predict((frame / 32768.0).astype(np.float32))
    assert "hey_jarvis" in scores
    assert 0.0 <= float(scores["hey_jarvis"]) <= 1.0

    prob = float(vad.predict(np.zeros(480, dtype=np.int16)))
    assert 0.0 <= prob <= 1.0
```

- [ ] **Step 2: Run test to verify it fails (or skips)**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests\test_voice_session.py::test_real_wake_model_and_vad_load -v`
Expected: PASS (or SKIP if `openwakeword` is missing). If it fails, it loads real engines against a silent frame — the assertion should hold.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_voice_session.py
git commit -m "test: real openWakeWord model smoke test"
```

---

## Task 6: Wire the new WS protocol into the websocket router

**Files:**
- Modify: `backend/app/routers/websocket.py`

**Interfaces:**
- Consumes: `VoiceSession` from Tasks 1–4; `safe_send(websocket, payload)` (already defined at websocket.py:608); `introduction_pending` (websocket.py:504); `settings_service.get(profile_id, "voice", "wake_word_sensitivity")`; `_build_system_prompt(extra, message, profile_id)` (websocket.py:47).
- Produces module-level registry `voice_sessions: dict[int, VoiceSession] = {}` (keyed by `id(websocket)`), and handlers `handle_voice_mode_start(websocket, profile_id)`, `handle_audio_frame(websocket, message)`, `handle_tts_done(websocket)`, `handle_voice_mode_stop(websocket)`, plus a re-pointed `handle_wake_word_config(websocket, message)`.

- [ ] **Step 1: Add the handlers**

In `backend/app/routers/websocket.py`, add near the other wake-word handlers (websocket.py:2631):

```python
voice_sessions: dict[int, VoiceSession] = {}


async def handle_voice_mode_start(websocket: WebSocket, profile_id: str):
    from app.services.settings_service import settings_service

    ws_id = id(websocket)
    if ws_id in voice_sessions:
        return
    threshold = float(settings_service.get(profile_id, "voice", "wake_word_sensitivity") or 0.5)
    session = VoiceSession(
        send=lambda payload: safe_send(websocket, payload),
        profile_id=profile_id,
        threshold=threshold,
        build_system_prompt=lambda message, pid: _build_system_prompt("", message, pid),
        is_introduction=lambda: ws_id in introduction_pending,
        on_intro_complete=lambda: introduction_pending.discard(ws_id),
    )
    result = await session.start()
    if result.get("status") == "success":
        voice_sessions[ws_id] = session


async def handle_audio_frame(websocket: WebSocket, message: dict):
    session = voice_sessions.get(id(websocket))
    if session is not None:
        await session.feed_pcm(message.get("audio", ""))


async def handle_tts_done(websocket: WebSocket):
    session = voice_sessions.get(id(websocket))
    if session is not None:
        await session.on_tts_done()


async def handle_voice_mode_stop(websocket: WebSocket):
    ws_id = id(websocket)
    session = voice_sessions.pop(ws_id, None)
    if session is not None:
        await session.stop()
```

Add the import at the top of the file (near line 15): `from app.services.voice_session_service import VoiceSession`.

- [ ] **Step 2: Add dispatch branches**

In `websocket_endpoint`'s message loop (websocket.py:664-827), add these branches before the existing `else`:

```python
            elif msg_type == "voice_mode_start":
                await handle_voice_mode_start(websocket, ci.profile_id)
            elif msg_type == "audio_frame":
                await handle_audio_frame(websocket, message)
            elif msg_type == "tts_done":
                await handle_tts_done(websocket)
            elif msg_type == "voice_mode_stop":
                await handle_voice_mode_stop(websocket)
```

- [ ] **Step 3: Re-point the existing `wake_word_config` handler**

Replace the body of `handle_wake_word_config` (websocket.py:2660-2676) so it no longer touches `wake_word_service`:

```python
async def handle_wake_word_config(websocket: WebSocket, message: dict):
    session = voice_sessions.get(id(websocket))
    if session is None:
        await safe_send(websocket, {"type": "wake_word_config", "config": {"active": False}})
        return
    sensitivity = message.get("sensitivity")
    if sensitivity is not None:
        session.set_threshold(float(sensitivity))
    keywords = message.get("keywords") or message.get("phrases")
    if keywords:
        session.set_keywords(keywords)
    await safe_send(websocket, {"type": "wake_word_config", "config": session.get_config()})
```

- [ ] **Step 4: Add disconnect teardown**

In the `except WebSocketDisconnect:` block (websocket.py:829-853), after `introduction_pending.discard(client_id)`, add:

```python
        session = voice_sessions.pop(client_id, None)
        if session is not None:
            await session.stop()
```

- [ ] **Step 5: Verify existing suite stays green**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests -q`
Expected: PASS (all existing tests; the new `test_voice_session.py` too)

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/websocket.py
git commit -m "feat: wire voice_mode WS protocol into websocket router"
```

---

## Task 7: Remove legacy wake-word and voice_chunk paths

**Files:**
- Modify: `backend/app/routers/websocket.py`
- Delete: `backend/app/services/wake_word_service.py`

**Interfaces:**
- Consumes: `strip_wake_phrase` now lives in `voice_session_service.py` (used internally by the session; nothing in `websocket.py` needs it anymore).
- Produces: a router free of `wake_word_service`, `handle_voice_chunk`, `_process_voice_command`, `client_voice_state`, and the old `wake_word_start`/`wake_word_stop` messages. This is a pure deletion task — no behavior change to the new protocol.

- [ ] **Step 1: Remove the old command-registry wake word handlers**

In `websocket_endpoint`'s handler-registration block, delete these lines (websocket.py:206-224):

```python
    from app.services.wake_word_service import wake_word_service

    async def wake_word_start_handler() -> dict:
        return await wake_word_service.start()

    async def wake_word_stop_handler() -> dict:
        return await wake_word_service.stop()

    async def wake_word_config_handler(setting: str = "", value: str = "") -> dict:
        if setting and value:
            if setting == "sensitivity":
                wake_word_service.set_sensitivity(float(value))
            elif setting == "keywords" or setting == "phrases":
                wake_word_service.set_keywords(value.split(","))
        return {"status": "success", "config": wake_word_service.get_config()}

    command_registry.register_handler("wake_word_start", wake_word_start_handler)
    command_registry.register_handler("wake_word_stop", wake_word_stop_handler)
    command_registry.register_handler("wake_word_config", wake_word_config_handler)
```

Keep the `briefing` handlers above them and `routine_service` block below them intact.

- [ ] **Step 2: Remove the `voice_chunk` dispatch branch**

Delete from the message loop (websocket.py:670-671):

```python
            if msg_type == "voice_chunk":
                asyncio.create_task(handle_voice_chunk(websocket, message, ci.profile_id))
```

- [ ] **Step 3: Remove the `wake_word_start` / `wake_word_stop` dispatch branches**

Delete from the message loop (websocket.py:782-785):

```python
            elif msg_type == "wake_word_start":
                await handle_wake_word_start(websocket)
            elif msg_type == "wake_word_stop":
                await handle_wake_word_stop(websocket)
```

Keep the `wake_word_config` branch (re-pointed in Task 6).

- [ ] **Step 4: Remove dead state and helpers**

- Delete `client_voice_state: dict[int, dict] = {}` (websocket.py:505) and its teardown line `client_voice_state.pop(client_id, None)` (websocket.py:837).
- Delete `_WAKE_PHRASE_PATTERNS` and `_strip_wake_phrase` (websocket.py:19-31) — the logic now lives in `voice_session_service.strip_wake_phrase`.

- [ ] **Step 5: Remove the old voice handlers**

- Delete `handle_voice_chunk` (websocket.py:1052-1182).
- Delete `_process_voice_command` (websocket.py:1185-1366). Note: `handle_text_message` at websocket.py:1368+ is untouched — its own introduction branch and command execution stay as-is for the text path.

- [ ] **Step 6: Remove the old wake-word WS handlers**

- Delete `handle_wake_word_start` (websocket.py:2633-2648) and `handle_wake_word_stop` (websocket.py:2651-2657). Keep the re-pointed `handle_wake_word_config`.

- [ ] **Step 7: Delete the deprecated service and verify**

```bash
git rm backend/app/services/wake_word_service.py
```

Then, from `backend\`:
1. `.\.venv\Scripts\python.exe -m pytest tests -q` — Expected: PASS.
2. `.\.venv\Scripts\python.exe -c "import app.main; import app.routers.websocket"` — Expected: no error.
3. Verify no lingering references: search `backend\app` for `wake_word_service`, `handle_voice_chunk`, `_process_voice_command`, `client_voice_state`, `_strip_wake_phrase` — Expected: zero matches (the WS message type string `wake_word_config` and `wake_word_detected`/`wake_word_result` remain and are intentional).

- [ ] **Step 8: Commit**

```bash
git add -A backend/app/routers/websocket.py
git rm --cached backend/app/services/wake_word_service.py 2>$null
git add -u
git commit -m "refactor: remove legacy wake word and voice_chunk paths"
```

(Use `git add` for the modified `websocket.py` and `git rm` for the deleted service; the exact staging commands may differ — stage only these two paths.)

---

## Task 8: Client — streaming frame pump in voice_service.dart

**Files:**
- Modify: `client/lib/services/voice_service.dart`

**Interfaces:**
- Consumes: existing `WebSocketService.send({...})`, `MicRecorder.pcm` (Android), ffmpeg `Process.start` (Windows), `_ttsChannel.invokeMethod('playAudio'/'stopAudio')` (Android — verified: `playAudio` resolves its result only when playback completes or is stopped, so `await` is a reliable natural-end signal). `home_screen.dart` still consumes `avatarState`, `transcription`, `response`, `ttsDone`, `exitApp`, `isListening`, `voicePhase` — all kept.
- Produces: `enum VoicePhase { idle, listening, command, thinking, speaking }`; `Stream<VoicePhase> get phase`; `_playbackInterrupted` guard so interrupted playback never sends `tts_done`; client→server messages `voice_mode_start`, `audio_frame`, `tts_done`, `voice_mode_stop`. Removes `VadState` entirely.

- [ ] **Step 1: Make the edit — enum, fields, and getters**

Replace the enum (line 11) and update fields:

```dart
enum VoicePhase { idle, listening, command, thinking, speaking }
```

Remove: `enum VadState`, `_vadStateController` (line 29), `_vadState` (line 33), `vadState` getter (line 59), `_audioBuffer` (line 35), `_silenceFrames`/`_speechFrames` (lines 36-37), `_isProcessing` (line 38), `_wakeWordCooldown` (line 41), `_speechThreshold`/`_speechStartFrames`/`_silenceEndFrames`/`_minSpeechFrames`/`_maxBufferSeconds` (lines 49-53), and `_frameSize` (line 48).

Add:

```dart
  final _phaseController = StreamController<VoicePhase>.broadcast();
  VoicePhase _phase = VoicePhase.idle;
  bool _playbackInterrupted = false;
  List<int> _frameBuffer = [];

  static const int _frameBytes = 1280 * 2; // 80 ms of s16 mono @ 16kHz
  static const int _framesPerMessage = 4;
```

Change the `_safeAdd(_vadStateController, ...)` usage in `dispose()` (line 642) to `_phaseController`, and add the getter next to the existing ones (after line 59):

```dart
  Stream<VoicePhase> get phase => _phaseController.stream;
```

Keep `bool get isListening => _alwaysListening;` and `VoicePhase get voicePhase => _phase;`.

- [ ] **Step 2: Replace `_handleMessage`**

Replace the whole `_handleMessage` (lines 111-168) with:

```dart
  void _handleMessage(Map<String, dynamic> message) {
    final type = message['type'];
    switch (type) {
      case 'avatar_state':
        _currentState = message['state'];
        _safeAdd(_avatarStateController, message['state']);
        break;
      case 'voice_mode_ready':
        if (message['status'] == 'error') {
          print('[Voice] Voice mode error: ${message['message']}');
          _safeAdd(_avatarStateController, 'error');
          _setPhase(VoicePhase.idle);
          stopListening();
        } else {
          print('[Voice] Voice mode ready');
          _setPhase(VoicePhase.listening);
        }
        break;
      case 'voice_phase':
        _setPhase(_parsePhase(message['phase']));
        break;
      case 'wake_word_detected':
        print('[Voice] Wake word detected');
        if (_currentPlayer != null) _stopCurrentPlayer();
        _setPhase(VoicePhase.command);
        _safeAdd(_avatarStateController, 'listening');
        break;
      case 'voice_response':
        _safeAdd(_transcriptionController, message['transcription'] ?? '');
        _safeAdd(_responseController, message['response'] ?? '');
        if (message['exit_app'] == true) {
          _playAudioAndExit(message['audio']);
        } else {
          _playAudio(message['audio']);
        }
        break;
      case 'text_response':
        _safeAdd(_responseController, message['response'] ?? '');
        break;
      case 'voice_error':
        print('[Voice] Voice error: ${message['message']}');
        _safeAdd(_avatarStateController, 'error');
        _setPhase(VoicePhase.listening);
        break;
      case 'error':
        _safeAdd(_avatarStateController, 'error');
        break;
    }
  }

  VoicePhase _parsePhase(dynamic value) {
    switch (value) {
      case 'listening': return VoicePhase.listening;
      case 'command': return VoicePhase.command;
      case 'thinking': return VoicePhase.thinking;
      case 'speaking': return VoicePhase.speaking;
      default: return VoicePhase.idle;
    }
  }

  void _setPhase(VoicePhase value) {
    _phase = value;
    _safeAdd(_phaseController, value);
  }
```

- [ ] **Step 3: Update playback — barge-in, no mic pause, tts_done**

Replace `_stopCurrentPlayer` (lines 170-182):

```dart
  void _stopCurrentPlayer() {
    if (_currentPlayer != null || Platform.isAndroid) {
      _playbackInterrupted = true;
    }
    if (_currentPlayer != null) {
      try { _currentPlayer!.kill(); } catch (_) {}
      _currentPlayer = null;
    }
    if (Platform.isAndroid) {
      try { _ttsChannel.invokeMethod('stopAudio'); } catch (_) {}
    }
  }
```

In `_playAudio` (lines 186-255):
1. After `_stopCurrentPlayer();` add `_playbackInterrupted = false;`.
2. Delete the mic-pause block (lines 199-202):
   ```dart
   if (isListening && !_isDisposed) {
     await stopListening();
     print('[Voice] Paused mic during TTS playback');
   }
   ```
3. After the platform playback branch completes (i.e. after the Android `else if` block), replace the resume-mic block (lines 238-247):

   ```dart
       if (_playbackInterrupted) {
         _playbackInterrupted = false;
         print('[Voice] Playback interrupted by barge-in, skipping tts_done');
         return;
       }

       _currentPlayer = null;
       print('[Voice] TTS playback done');
       _safeAdd(_ttsDoneController, null);
       if (!_isDisposed && !_exitPending) {
         _webSocketService.send({'type': 'tts_done'});
       }
   ```

   (Delete the old `await Future.delayed(...); startListening();` block — the mic never stops during playback now.)

- [ ] **Step 4: Replace the frame pump**

Replace `_processAudioStream` (lines 432-459) and delete `_processFrame` (461-516) and `_sendBufferedAudio` (518-574) and the WAV builder:

```dart
  void _processAudioStream(Stream<List<int>> audioStream) {
    _audioStreamSub?.cancel();
    _audioStreamSub = audioStream.listen(
      (data) {
        _frameBuffer.addAll(data);
        while (_frameBuffer.length >= _framesPerMessage * _frameBytes) {
          final chunk = _frameBuffer.sublist(0, _framesPerMessage * _frameBytes);
          _frameBuffer.removeRange(0, _framesPerMessage * _frameBytes);
          _sendAudioFrame(chunk);
        }
      },
      onDone: () => print('[Voice] Audio stream ended'),
      onError: (e) => print('[Voice] Audio stream error: $e'),
    );
  }

  void _sendAudioFrame(List<int> pcm) {
    _webSocketService.send({
      'type': 'audio_frame',
      'audio': base64Encode(Uint8List.fromList(pcm)),
    });
  }
```

- [ ] **Step 5: Update start/stop**

Replace `startWakeWordMode` (lines 392-399):

```dart
  Future<bool> startWakeWordMode() async {
    if (_isDisposed) return false;
    _wakeWordMode = true;
    _setPhase(VoicePhase.idle);
    final started = await startListening();
    if (!started) {
      _wakeWordMode = false;
      return false;
    }
    _webSocketService.send({'type': 'voice_mode_start', 'sample_rate': _sampleRate});
    return true;
  }
```

Replace `stopListening` (lines 576-619):

```dart
  Future<void> stopListening() async {
    if (!_alwaysListening && !_wakeWordMode) return;
    _alwaysListening = false;
    _wakeWordMode = false;
    _setPhase(VoicePhase.idle);
    try { _webSocketService.send({'type': 'voice_mode_stop'}); } catch (_) {}
    try { await _audioStreamSub?.cancel(); } catch (_) {}
    _audioStreamSub = null;
    _frameBuffer.clear();
    if (Platform.isAndroid) {
      await _micRecorder?.stop();
    } else if (_recordingProcess != null) {
      try {
        _recordingProcess!.stdin.write('q');
        await _recordingProcess!.stdin.flush();
      } catch (_) {}
      await _stderrSub?.cancel();
      await _stdoutSub?.cancel();
      final exitCode = await _recordingProcess!.exitCode.timeout(
        Duration(seconds: 3),
        onTimeout: () {
          _recordingProcess?.kill();
          return -1;
        },
      );
      print('[Voice] ffmpeg exit: $exitCode');
      _recordingProcess = null;
    }
    _safeAdd(_avatarStateController, 'idle');
  }
```

Update `dispose()` (lines 629-643): remove the `_vadStateController.close()` line, add `if (!_phaseController.isClosed) _phaseController.close();`, and remove `_micRecorder?.stop()` duplicate concern (keep it).

- [ ] **Step 6: Run the analyzer**

Run from `client\`: `flutter analyze`
Expected: No new errors or warnings in `voice_service.dart`.

- [ ] **Step 7: Commit**

```bash
git add client/lib/services/voice_service.dart
git commit -m "feat: client streams PCM frames, removes energy VAD"
```

---

## Task 9: Client — phase-driven UI and auto-start gate in home_screen.dart

**Files:**
- Modify: `client/lib/screens/home_screen.dart`

**Interfaces:**
- Consumes: `VoiceService.phase` stream (Task 8), `VoicePhase` enum (Task 8), `SettingsService.fetch()` + `wakeWordEnabled` getter, `ServerConfig.load()`.
- Produces: auto-start of wake-word mode gated on the `wake_word_enabled` setting; status text keyed off `voice_phase`.

- [ ] **Step 1: Add settings access**

Add imports at the top:

```dart
import '../services/settings_service.dart';
import '../services/server_config.dart';
```

Add a field next to `late VoiceService _voiceService;` (line 26):

```dart
  SettingsService? _settingsService;
```

In `initState` (after `_voiceService = VoiceService(...)`), call `_loadSettings();` and add:

```dart
  Future<void> _loadSettings() async {
    try {
      final config = await ServerConfig.load();
      if (config == null || !mounted) return;
      final settings = SettingsService(config);
      await settings.fetch();
      if (!mounted) return;
      setState(() => _settingsService = settings);
    } catch (_) {}
  }
```

- [ ] **Step 2: Replace VadState with phase**

- Change the field initializer `VoicePhase _voicePhase = VoicePhase.wakeWord;` (line 35) to `VoicePhase _voicePhase = VoicePhase.idle;`.
- Rename `StreamSubscription? _vadSubscription;` (line 44) to `_phaseSubscription`.
- Replace the `_vadSubscription` listener (lines 110-114):

```dart
    _phaseSubscription = _voiceService.phase.listen((phase) {
      if (mounted && _wakeWordMode) {
        setState(() {
          _isListening = phase != VoicePhase.idle;
          _voicePhase = phase;
        });
      }
    });
```

- In the `_ttsDoneSubscription` block (lines 85-98), gate the auto-start:

```dart
    _ttsDoneSubscription = _voiceService.ttsDone.listen((_) {
      if (!_greetingReceived && mounted) {
        _greetingReceived = true;
        Future.delayed(Duration(milliseconds: 500), () async {
          if (!mounted) return;
          final enabled = _settingsService?.wakeWordEnabled ?? true;
          if (!enabled) return;
          final started = await _voiceService.startWakeWordMode();
          if (mounted) setState(() {
            _wakeWordMode = started;
            _voicePhase = VoicePhase.idle;
          });
        });
      }
    });
```

- In `dispose()` (find the `_vadSubscription?.cancel()` call), rename to `_phaseSubscription`.

- [ ] **Step 3: Replace the status-text switch**

Replace `_buildBottomPanel`'s status switch (lines 320-339) with:

```dart
    String status = _avatarState == 'error'
        ? 'Something went wrong. Try again.'
        : switch (_voicePhase) {
            VoicePhase.idle =>
                _wakeWordMode ? 'Say "Hey Jarvis" to activate' : 'Type a message below to chat',
            VoicePhase.listening => 'Say "Hey Jarvis" to activate',
            VoicePhase.command => 'Listening for command...',
            VoicePhase.thinking => 'Processing...',
            VoicePhase.speaking => 'Speaking...',
          };
```

- [ ] **Step 4: Run the analyzer**

Run from `client\`: `flutter analyze`
Expected: No new errors or warnings.

- [ ] **Step 5: Commit**

```bash
git add client/lib/screens/home_screen.dart
git commit -m "feat: client drives voice UI from server voice_phase"
```

---

## Task 10: Documentation updates

**Files:**
- Modify: `vault/API_DOCS.md`, `vault/Voice Pipeline.md`, `vault/AGENTS.md`, `vault/memory/Decisions/openWakeWord over Whisper for wake word.md`

**Interfaces:** none (docs only).

- [ ] **Step 1: Update `vault/API_DOCS.md`**

- Add client→server messages: `voice_mode_start`, `audio_frame`, `tts_done`, `voice_mode_stop`; note `wake_word_config` is kept.
- Add server→client messages: `voice_mode_ready`, `voice_phase`, `wake_word_detected`, `voice_error`.
- Remove `voice_chunk`, `wake_word_miss`, `wake_word_error` from the documented protocol.
- Update the `voice_response` entry to note it now carries `{transcription, response, audio, model}` plus optional `is_farewell`/`exit_app`/`is_introduction`.

- [ ] **Step 2: Update `vault/Voice Pipeline.md`**

Describe the new flow: client streams continuous 16kHz s16 PCM → server `VoiceSession` (LISTENING → COMMAND → THINKING → SPEAKING), openWakeWord frame-by-frame, Silero VAD endpointing, barge-in, `tts_done` → LISTENING.

- [ ] **Step 3: Update `vault/AGENTS.md`**

Replace references to `wake_word_service.py` with `voice_session_service.py` (`VoiceSession` per-connection state machine).

- [ ] **Step 4: Update the decision note**

In `vault/memory/Decisions/openWakeWord over Whisper for wake word.md`, add a dated note (2026-08-05): openWakeWord is now the core of a streaming server-driven voice loop (`VoiceSession`), replacing the post-hoc whole-clip classification; link to `docs/superpowers/specs/2026-08-05-voice-mode-openwakeword-design.md`.

- [ ] **Step 5: Remove dead references**

Search `vault\` for `client_voice_state` and `wake_word_service` and update/remove stale mentions so nothing points at the deleted code.

- [ ] **Step 6: Commit**

```bash
git add vault/API_DOCS.md vault/Voice\ Pipeline.md vault/AGENTS.md vault/memory/Decisions/openWakeWord\ over\ Whisper\ for\ wake\ word.md
git commit -m "docs: update vault for streaming voice mode"
```

---

## Task 11: Final verification and manual QA runbook

**Files:** none.

- [ ] **Step 1: Backend suite**

Run from `backend\`: `.\.venv\Scripts\python.exe -m pytest tests -q`
Expected: PASS, including `test_voice_session.py` and the unchanged `test_commands.py` / `test_api.py`.

- [ ] **Step 2: Import sanity**

Run from `backend\`: `.\.venv\Scripts\python.exe -c "import app.main; import app.routers.websocket"` — Expected: no error.

- [ ] **Step 3: Client analyzer**

Run from `client\`: `flutter analyze` — Expected: clean.

- [ ] **Step 4: Manual QA checklist** (backend running via `run-backend.ps1` in a detached window, per AGENTS.md)

1. Wake: app connects, greeting plays, then mic stays on and "Say 'Hey Jarvis' to activate" shows. Saying "hey jarvis" transitions to "Listening for command...".
2. One-breath command: "hey jarvis turn on the lights" executes without a second wait.
3. Wake-word-every-turn: after a response, no follow-up window; must say "hey jarvis" again.
4. Barge-in: while JARVIS is speaking, say "hey jarvis" — playback stops immediately and the new command is captured.
5. Empty/noise: coughs or silence after wake return silently to LISTENING (no error).
6. First-time user: on a fresh profile (delete `backend/data/personality/<id>/style.json` or set `introduced: false`), the greeting asks the name; speaking it saves `preferred_name` and the next greeting uses it.
7. Goodbye: "hey jarvis goodbye" plays farewell and exits.
8. Toggle: disable Voice Input in Settings; reconnect — wake-word mode does not auto-start.

---

## Self-Review (run after writing the plan)

**1. Spec coverage** — mapped:
- always-on frame-by-frame wake detection → Task 2; Silero VAD command capture → Task 3; barge-in → Task 2 + Task 8; introduction → Task 4 + Task 9/11; config wiring (`wake_word_sensitivity` → threshold, `wake_word_enabled` gates auto-start) → Task 6 + Task 9; new WS protocol + removed messages → Tasks 6-8; deprecations (`wake_word_service`, `client_voice_state`, `voice_chunk`) → Task 7; per-session models + `asyncio.to_thread` → Tasks 1-2; error handling (engine failure → `voice_mode_ready error`; STT/LLM/TTS failure → `voice_error`; empty STT → silent LISTENING; disconnect teardown) → Tasks 1, 4, 6; tests (fake detectors, endpointing, intro, suppression, tts_done, stop, smoke skip, existing suites green) → Tasks 1-5, 11; client design (delete VAD state, streaming pump, phase enum, no mic pause, tts_done) → Task 8; home_screen phase UI + status text → Task 9; docs → Task 10; non-goals untouched → Global Constraints.

**2. Placeholder scan** — no TBD/TODO/"similar to" patterns; every code step contains full code. Task 7 uses function names + start lines rather than blind line ranges, which is safer in a 2950-line file.

**3. Type consistency** — `VoiceSession(send, profile_id=..., threshold=..., ...)` matches constructor; `_wake_scan`/`_vad_scan`/`_track_vad`/`_finalize`/`_emit_error`/`_reset_command_buffers` names match Tasks 1-4; `voice_sessions` keyed by `id(websocket)` matches both handlers and disconnect; `strip_wake_phrase` lives in `voice_session_service` only; client `VoicePhase` values match server `SessionPhase` string values; `_frameBytes = 1280 * 2` and `_framesPerMessage = 4` used consistently in the pump.
