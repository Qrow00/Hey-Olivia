# Voice Mode Rebuild Around openWakeWord — Design

Date: 2026-08-05
Status: Approved (pre-implementation)
Scope: Backend + Flutter client voice pipeline

## Summary

Rebuild JARVIS voice mode so openWakeWord is the core of an always-on,
server-driven, streaming voice loop. The client becomes a thin audio pump that
streams raw PCM frames over WebSocket; the backend runs a per-connection
`VoiceSession` state machine that does openWakeWord wake-word detection
frame-by-frame, Silero VAD command capture, STT, command/LLM handling, and TTS.
Supports wake-word barge-in during playback. Deferred: on-device Android
detection (swap the detection engine behind an interface later).

## Problem with the current implementation

- openWakeWord is used post-hoc: the client runs energy-based VAD, buffers a
  whole utterance, and only then sends it; the server classifies the entire
  clip at once (`wake_word_service.process_bytes`). "Hey Jarvis" must be an
  isolated utterance with silence around it; detection latency is ~1s+.
- The server-side command state machine (`client_voice_state`) is dead code.
- Client cooldown/miss handling is client-side and fragile.
- No barge-in; mic is paused during TTS playback.

## Architecture

Client streams 16kHz mono s16 PCM continuously while in wake-word mode. The
server owns the full voice loop in a per-connection `VoiceSession`:

- **LISTENING** — openWakeWord (`hey_jarvis`) runs frame-by-frame (1280
  samples/80ms). Score > threshold → send `wake_word_detected`, `model.reset()`,
  enter COMMAND. Frames after the detected frame flow into the command buffer
  (supports "hey jarvis turn on the lights" in one breath).
- **COMMAND** — Silero VAD (`openwakeword.vad.VAD`, bundled silero_vad.onnx, no
  new dependency) detects speech onset; buffers until end-of-speech or
  max-duration. Then THINKING → STT → command registry / LLM → TTS → send
  `voice_response`, enter SPEAKING.
- **SPEAKING** — wake model stays active. Re-detection → client stops playback,
  enter COMMAND (barge-in). On client `tts_done` → LISTENING. No follow-up
  window: wake word required every turn.

## Backend design

### New service: `backend/app/services/voice_session_service.py`

```python
class SessionPhase(Enum):
    LISTENING = "listening"
    COMMAND   = "command"
    THINKING  = "thinking"
    SPEAKING  = "speaking"

class VoiceSession:
    def __init__(self, websocket, profile_id, send_lock): ...
    phase: SessionPhase
    _wake_model: OwwModel | None       # openwakeword.Model, per-session, lazy
    _vad: openwakeword.vad.VAD | None  # silero_vad.onnx, per-session
    _command_buffer: bytearray         # raw s16 PCM from detection onward
    _in_speech: bool
    _speech_frames: int                # onset counter (VAD p > 0.5)
    _silence_frames: int               # offset counter (VAD p < 0.5)
    _last_detection: float             # suppression / barge-in guard
```

Public API consumed by the WS handler:
- `async start() -> dict` — create worker task, lazily load engines off-thread,
  emit `voice_mode_ready`.
- `async feed_pcm(audio_b64: str)` — decode, enqueue for the worker.
- `async on_tts_done()` — SPEAKING → LISTENING.
- `async stop()` — cancel worker, drop models.
- `set_threshold(value)` / `set_keywords(list)` — wired to `wake_word_config`.

Per-session model instances: openWakeWord keeps internal rolling state
(`prediction_buffer`), so concurrent connections cannot share one `Model`. Each
session lazily creates its own `OwwModel` + `VAD` (~50MB each; fine for a 1–2
client home server). Loaded via `asyncio.to_thread`.

### Frame handling (worker task, synchronous)

1. Decode base64 → int16 PCM → accumulate into a small `bytearray`.
2. Pop exact 1280-sample (2560-byte) frames; feed each to the wake model as
   `float32 / 32768` (or int16 directly for `VAD.predict`).
3. Wake path: `pred = _wake_model.predict(frame)`; detect when
   `pred.get("hey_jarvis", 0) > threshold`.
4. VAD path: split frame into 480-sample chunks, `vad.predict(chunk)`.

### Command endpointing thresholds

- onset: 5 consecutive VAD frames > 0.5 (~150ms) → start buffering
- offset: 30 consecutive frames < 0.5 (~900ms) → end-of-speech → finalize
- guards: min command 0.4s, max 12s (force-finalize)

### Finalize path (end-of-speech)

- phase → THINKING; send `avatar_state: thinking`
- if ws id in `introduction_pending`: treat transcription as the user's name
  (capitalize, alpha-only; fallback "Boss"), save to personality profile
  (`preferred_name`, `introduced = True`), discard from set, reply "Nice to meet
  you, {name}! How may I assist you today?" — this replaces the old
  `voice_chunk` introduction branch.
- else: `speech_to_text` → if empty return to LISTENING silently →
  `command_registry.parse_command` (matched: execute; else LLM
  `chat_completion`) → `text_to_speech` → send `voice_response` → SPEAKING.

### Concurrency

- One worker task per session consuming an `asyncio.Queue`; frames process in
  order. predict ≈ 1–2ms/frame at 12.5 fps — no event-loop blocking concern.
- STT/LLM/TTS offloaded via `asyncio.to_thread` / `asyncio.create_task`
  (existing patterns in `voice_service.py` / `websocket.py`).
- All outbound sends serialize through a per-session `asyncio.Lock`.

### Deprecations

- `wake_word_service.py` replaced by `VoiceSession` (no shared model, no
  `process_bytes` on whole clips). `wake_word_start/stop/config` handlers become
  thin wrappers over `voice_mode_start/stop/config`.

## WebSocket protocol

### Client → Server

| type | payload | notes |
|------|---------|-------|
| `voice_mode_start` | `{sample_rate: 16000}` | create session, load engines |
| `audio_frame` | `{audio: base64(pcm)}` | raw s16 PCM; continuous while awake |
| `tts_done` | `{}` | playback finished → SPEAKING → LISTENING |
| `voice_mode_stop` | `{}` | tear down session |
| `wake_word_config` | `{setting, value}` | threshold / keywords (kept) |

### Server → Client

| type | payload | notes |
|------|---------|-------|
| `voice_mode_ready` | `{status}` | engines loaded, streaming may begin |
| `voice_phase` | `{phase}` | explicit state sync |
| `wake_word_detected` | `{timestamp}` | also means "interrupt playback" in SPEAKING |
| `avatar_state` | `{state}` | existing (listening/thinking/speaking/idle/error) |
| `voice_response` | `{transcription, response, audio, model}` | existing shape; keeps `exit_app`/`is_farewell` |
| `voice_error` | `{message}` | new; replaces ad-hoc error TTS |
| `wake_word_result` / config | | existing |

Removed: `voice_chunk` (replaced by `audio_frame`), `wake_word_miss`,
client-side `wake_word_start/stop` (wrappers only).

Disconnect: session torn down in the existing `finally` block
(`websocket.py:830`): worker cancelled, models released, `introduction_pending`
cleaned.

## Client design (Flutter)

`client/lib/services/voice_service.dart`:
- Streaming pump replaces energy VAD: keep ffmpeg (Windows) / MicRecorder
  (Android) 16kHz mono s16 capture; slice into 1280-sample frames; batch 4
  frames per `audio_frame` message (~3 msgs/s); keep leftover-buffer logic.
- Delete: `_processFrame` energy VAD, `_speechThreshold`, `_speechFrames`,
  `_silenceFrames`, `_audioBuffer`, `_sendBufferedAudio` + WAV header builder,
  `_wakeWordCooldown`, `wake_word_check`, `VadState` enum.
- Client phase enum mirrors server: `{idle, listening, command, thinking,
  speaking}`, updated from `voice_phase`; keep `isListening` / `voicePhase`
  getters.
- `_handleMessage`: `voice_mode_ready`, `voice_phase`, `wake_word_detected`,
  `voice_response`, `voice_error`; drop `wake_word_miss`.
- `startWakeWordMode()`: start mic → send `voice_mode_start` → stream frames.
  On `voice_mode_ready: error` → show error, don't stream.
- `_playAudio`: do NOT pause the mic during playback (barge-in requires the
  stream). On `wake_word_detected` while a player is active →
  `_stopCurrentPlayer()` (kills powershell process / Android `stopAudio`). After
  natural playback end → send `tts_done`.
- `stopListening()`: stop mic, send `voice_mode_stop`, reset to idle.
- `_playAudioAndExit` / farewell unchanged.

`client/lib/screens/home_screen.dart`: drive UI off `voice_phase` instead of
`VadState`; status text "Say 'Hey Jarvis' to activate" / "Listening for
command..." / "Speaking...". Avatar widget unchanged (consumes `avatar_state`).

Android native plugins untouched — `MicRecorderPlugin` (16kHz mono PCM stream)
and `TTSPlugin` (stoppable MediaPlayer) already support the new flow.

## Config

- `settings_service`: `wake_word_enabled` gates auto-start; `wake_word_sensitivity`
  (0.5) → detection threshold, read at session start, updated live by
  `wake_word_config`.
- Keywords map unchanged: "hey jarvis" → `hey_jarvis` (default); "alexa",
  "hey mycroft", "hey rhasspy" available.

## Error handling

- Engine load failure → `voice_mode_ready: {status: error}` → client error state,
  stays idle, no streaming.
- WS disconnect → session teardown in `finally` (worker cancelled, models
  released, `introduction_pending` cleaned).
- Empty/no transcription → silent return to LISTENING.
- STT/LLM/TTS failure → `voice_error` + return to LISTENING.
- Barge-in / `tts_done` races → 1s suppression window after any detection +
  phase guards.

## Testing

Backend (`pytest` + `pytest-asyncio`, in `backend/tests/`), with injected fake
detectors (no real model needed, deterministic):
- wake detection: LISTENING → COMMAND; detection during SPEAKING → barge-in
- endpointing: scripted VAD probabilities → onset/offset → finalize; min/max
  duration guards; empty STT → LISTENING
- introduction path: `introduction_pending` → name captured, flag cleared
- suppression window; `tts_done` → LISTENING; `stop()` cleanup
- one model smoke test (skipped if openwakeword missing): `OwwModel` loads
  `hey_jarvis`, `VAD` loads
- existing `test_commands.py` / `test_api.py` stay green

Client: `flutter analyze`; manual QA checklist (wake, one-breath command,
barge-in, goodbye/exit).

## Docs to update

- `vault/API_DOCS.md` — new message types, removed `voice_chunk`/`wake_word_miss`
- `vault/Voice Pipeline.md` — streaming flow
- `vault/AGENTS.md` — replace `wake_word_service.py` with `voice_session_service.py`
- `vault/memory/Decisions/openWakeWord over Whisper for wake word.md` — note the rebuild
- remove dead `client_voice_state` references

## Non-goals

- On-device (Flutter-side) wake detection — deferred; `VoiceSession` isolates the
  detection engine so it can be swapped later.
- Multi-turn follow-up windows — wake word required every turn.
- PTT mode — not wired in the current UI; `push_to_talk` setting untouched.
