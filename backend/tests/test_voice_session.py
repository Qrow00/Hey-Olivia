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
