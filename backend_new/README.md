# J.A.R.V.I.S. V4 - Agent Core

A server-based personal assistant: **JARVIS V4** is the LLM-free successor to the V3
prototype. It understands commands through a fast pure-Python NLU pipeline, runs
skills (media, smart home, browser, email, docs, camera, Android/ADB, code
scaffolding, scheduler, system control), talks to you in a British JARVIS voice,
and is controlled from a self-contained web UI.

- V3 code is archived under `backend_new/legacy_v3/`.
- Flutter client sources live under `client_new/` (not wired to V4 yet).

## Quickstart

```powershell
cd backend_new
python -m pip install -r requirements_new.txt   # edge-tts gives JARVIS voice
.\run-backend.ps1                                # starts uvicorn on :8000
```

Open http://127.0.0.1:8000 in a browser. Type "what time is it", "play some
music", "remind me to buy groceries", or click a QUICK tile. Click **TEST
VOICE** (SYSTEM tab) to hear JARVIS speak.

Run tests:

```powershell
cd backend_new
python -m pytest
```

## How it works

```
text/voice ─► NLU pipeline ─► skill execution ─► narration + (optionally) TTS
                  │
                  ├─ fast-path regex patterns  (patterns.py, <10ms)
                  ├─ Naive Bayes classifier    (trainable, no ML deps)
                  └─ else: chat                (llama-server / GGUF / template)
```

- `app/nlu/` — regex fast-path, classifier, entity extraction, seed data.
- `app/skills/` — every capability is a module exposing `register(reg)`.
- `app/core/` — `SkillRegistry` (skill registry) and `AgentKernel` (services).
- `app/api/` — REST (`/command`, `/tts`, `/teach`, `/feedback`, `/faces`,
  `/schedule`, `/personality`) + WebSocket `/ws` gateway.
- `app/chat/` — personality sliders (drive chat prompt + TTS voice/rate).
- `app/state_store.py` — per-profile state in SQLite + JSON (personality,
  schedule, settings).
- `app/vision/`, `app/voice/`, `app/learner/`, `app/memory/` — optional
  services gated by `JARVIS_SERVICES`.

## Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `JARVIS_HOST` | `0.0.0.0` | Bind address |
| `JARVIS_PORT` | `8000` | HTTP/WS port |
| `JARVIS_PROFILE` | `default` | Active profile |
| `JARVIS_SERVICES` | `full` | Space-separated: `memory voice vision learner` |
| `JARVIS_TOKEN` | *(empty)* | If set, REST + WS require it (`Authorization: Bearer`). Set before exposing beyond localhost. |
| `JARVIS_TTS_VOICE` | `en-GB-RyanNeural` | Default edge-tts voice |
| `JARVIS_STT_MODEL` | `small` | faster-whisper model size |
| `JARVIS_DATA_DIR` | `backend_new/data` | Capture dir, projects, vectors |
| `JARVIS_CHAT_API` | `http://127.0.0.1:8080/v1` | OpenAI-compatible chat endpoint |
| `JARVIS_USE_LLAMA_SERVER` | `false` | Use the chat endpoint before GGUF/fallback |
| `JARVIS_CHAT_GGUF` | `models/Llama-3.2-3B-Instruct-Q4_K_M.gguf` | In-process GGUF path |
| `JARVIS_EMAIL_IMAP_HOST/USER/PASSWORD` | — | Email reading |
| `JARVIS_EMAIL_SMTP_HOST/USER/PASSWORD` | — | Email sending |

Heavy dependencies are optional: install `edge-tts` for voice,
`faster-whisper` for speech-to-text, `opencv-python` + `onnxruntime` for
vision, `llama-cpp-python` for in-process chat. Everything else runs on the
stdlib + FastAPI.

## Adding a skill

1. Create `app/skills/mything.py` with an `async def do_thing(params, ctx)` that
   returns `{"success": bool, "narration": str, ...}` and a `register(reg)`
   that calls `reg.skill("mything_do", do_thing, description="...")`.
2. Add the module to `register_all` in `app/skills/__init__.py`.
3. (Optional) add a regex pattern in `app/nlu/patterns.py` so the phrase hits
   the fast path, and a seed example in `app/nlu/training_data.py`.
4. Test: `python -m pytest`.

## API notes

- `POST /command {"text": "..."}` — run a command; returns intent/confidence/narration.
- `POST /tts {"text": "..."}` — returns `audio_base64` (MP3) in the current voice.
- `POST /teach {"text": ..., "intent": ...}` — teach the classifier a new phrase.
- `POST /feedback` — record good/bad/wrong-intent feedback for the learner.
- `GET|POST /schedule`, `POST /schedule/clear` — persisted reminders/alarms.
  The server broadcasts `reminder_due` over WebSocket when an alarm fires.
- `GET /faces`, `POST /faces` — face database (vision service).
- `GET /personality`, `PUT /personality` — six sliders (humor, sarcasm, warmth,
  energy, formality, curiosity).
- `WS /ws` — message types: `text_command`, `voice_audio`, `personality_update`,
  `personality_get`, `teach_example`, `feedback`, `settings_update`,
  `plugin_control`, `knowledge_search`. Pass `?token=` when `JARVIS_TOKEN` is set.

## Known limitations

- Scheduler alarms fire only while the server is running (background task polls
  every ~20s; alarms are parsed as wall-clock times like "7 am").
- Chat needs a model: install a GGUF or run an OpenAI-compatible server, else
  JARVIS answers with personality-styled template replies.
- Weather, CCTV, and email require external configuration (API key / RTSP
  streams / IMAP-SMTP credentials).
