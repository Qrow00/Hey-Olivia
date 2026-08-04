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
    VAD_CHUNK_LENGTH,
    ONSET_FRAMES,
    OFFSET_FRAMES,
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


@pytest.mark.anyio
async def test_command_no_onset_times_out_to_listening(monkeypatch):
    clock = {"t": 100.0}
    monkeypatch.setattr("app.services.voice_session_service.time.monotonic", lambda: clock["t"])
    send = SendCollector()
    session = VoiceSession(send)
    session._wake_model = FakeWakeModel(score=0.9)
    session._vad = FakeVad([0.0])
    await session._process_audio(SILENT_FRAME)
    assert session.phase == SessionPhase.COMMAND
    clock["t"] += 3.1
    await session._process_audio(SILENT_FRAME)
    assert session.phase == SessionPhase.LISTENING
    phases = [m["phase"] for m in send.messages if m["type"] == "voice_phase"]
    assert phases == ["command", "listening"]


@pytest.mark.anyio
async def test_vad_scan_chunks_into_480_sample_units():
    send = SendCollector()
    session = VoiceSession(send)
    vad = FakeVad([0.5] * 10)
    session._vad = vad
    session.phase = SessionPhase.COMMAND
    await session._process_audio(SILENT_FRAME)
    assert len(vad.chunks) == 2
    assert all(len(c) == VAD_CHUNK_LENGTH for c in vad.chunks)
    assert all(c.dtype == np.int16 for c in vad.chunks)
    assert len(session._vad_buffer) == FRAME_BYTES - 2 * VAD_CHUNK_BYTES


@pytest.mark.anyio
async def test_track_vad_onset_sets_in_speech_after_five_chunks():
    send = SendCollector()
    session = VoiceSession(send)
    for _ in range(ONSET_FRAMES):
        await session._track_vad(0.9, bytes(VAD_CHUNK_BYTES))
    assert session._in_speech is True
    assert len(session._command_buffer) == VAD_CHUNK_BYTES


@pytest.mark.anyio
async def test_track_vad_offset_triggers_finalize():
    send = SendCollector()
    calls = []
    session = VoiceSession(send)

    async def finalize_stub():
        calls.append(True)

    session._finalize = finalize_stub
    session._in_speech = True
    for _ in range(OFFSET_FRAMES):
        await session._track_vad(0.1, bytes(VAD_CHUNK_BYTES))
    assert calls == [True]


def finalize_session(send, **kw):
    async def _speech_to_text(audio):
        return {"text": "turn on the lights", "confidence": 0.9}

    async def _text_to_speech(text):
        return b"MP3DATA"

    async def _chat_completion(msg, sp):
        return {"response": "Done.", "model": "llama3.2"}

    async def _execute_command(text):
        return {"result": {"status": "success", "message": "Lights on"}}

    defaults = dict(
        speech_to_text=_speech_to_text,
        text_to_speech=_text_to_speech,
        chat_completion=_chat_completion,
        parse_command=lambda text: {"matched": True, "handler": "lights", "category": "smart_home"},
        execute_command=_execute_command,
        get_profile=lambda pid: FakeProfile(),
    )
    defaults.update(kw)
    return VoiceSession(send, **defaults)


async def run_finalize(session, seconds=3.0):
    session.phase = SessionPhase.COMMAND
    session._command_buffer = bytearray(b"\x00\x00" * int(seconds * 16000))
    await session._finalize()


@pytest.mark.anyio
async def test_vad_endpointing_finalizes_command():
    send = SendCollector()
    session = finalize_session(send)
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
    session = finalize_session(send)
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
    session = finalize_session(send)
    session._wake_model = FakeWakeModel(score=0.0)
    session._vad = FakeVad([0.9] * 1000)
    session.phase = SessionPhase.COMMAND
    await session._process_audio(SILENT_FRAME * 205)
    assert any(m["type"] == "voice_response" for m in send.messages)
    assert session.phase == SessionPhase.SPEAKING


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

    async def empty_stt(audio):
        return {"text": "", "confidence": 0.0}

    session = finalize_session(send, speech_to_text=empty_stt)
    await run_finalize(session)
    assert not any(m["type"] == "voice_response" for m in send.messages)
    assert session.phase == SessionPhase.LISTENING


@pytest.mark.anyio
async def test_finalize_strip_wake_phrase_from_transcription():
    send = SendCollector()

    async def wake_stt(audio):
        return {"text": "hey jarvis set alarm", "confidence": 0.9}

    session = finalize_session(send, speech_to_text=wake_stt)
    await run_finalize(session)
    resp = [m for m in send.messages if m["type"] == "voice_response"][-1]
    assert resp["transcription"] == "set alarm"


@pytest.mark.anyio
async def test_introduction_captures_name():
    send = SendCollector()
    profile = FakeProfile()

    async def intro_stt(audio):
        return {"text": "alice smith", "confidence": 0.9}

    session = finalize_session(
        send,
        get_profile=lambda pid: profile,
        is_introduction=lambda: True,
        speech_to_text=intro_stt,
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

    async def empty_stt(audio):
        return {"text": "", "confidence": 0.0}

    session = finalize_session(
        send,
        get_profile=lambda pid: profile,
        is_introduction=lambda: True,
        speech_to_text=empty_stt,
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
