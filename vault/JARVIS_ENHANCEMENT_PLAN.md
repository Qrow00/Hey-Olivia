# Jarvis Enhancement Plan — 8 Phases

## Overview
10 new features to make Jarvis act and feel more like the real JARVIS from Iron Man.

**Approach:** Phased build, local-first, no unnecessary API costs.

---

## Phase 1: Proactive Monitoring & System Awareness
**Goal:** Jarvis watches the system and reports issues without being asked.

| Component | File | Description |
|---|---|---|
| System Monitor | `backend/app/services/monitoring_service.py` | Background task polling CPU/RAM/disk/GPU temps every 30s, stores in SQLite ring buffer |
| Alert Engine | `backend/app/services/alert_engine.py` | Threshold rules (disk > 90%, GPU > 85C, RAM > 85%) — triggers voice + notification |
| Activity Logger | `backend/app/services/activity_logger.py` | Logs running processes, active windows, file changes — stores for recall |
| WebSocket Events | `backend/app/routers/websocket.py` | `system_alert`, `activity_update` pushed to Flutter client |

**New command handlers:**
- `system_health` — current CPU/RAM/disk/GPU stats
- `get_alerts` — recent system alerts
- `get_activity_log` — recent activity
- `set_alert_threshold` — configure alert thresholds

---

## Phase 2: Morning Briefing
**Goal:** One voice readout with everything important on connect.

| Component | File | Description |
|---|---|---|
| Briefing Orchestrator | `backend/app/services/briefing_service.py` | Calls weather, system, news, calendar, smart home — assembles text |
| Weather Service | `backend/app/services/weather_service.py` | Open-Meteo API (free, no key) — current conditions + forecast |
| News Service | `backend/app/services/news_service.py` | RSS feeds (configurable) — top 5 headlines via feedparser |
| Calendar Service | `backend/app/services/calendar_service.py` | Google Calendar API (OAuth) — today's events |
| Smart Home Status | Reuse `mqtt_service.py` | Query device states |
| System Health | Reuse `monitoring_service.py` | From Phase 1 |
| Voice Readout | `backend/app/services/voice_service.py` | Text → edge-tts → stream to client on connect |

**New command handlers:**
- `morning_briefing` — trigger full briefing
- `briefing_config` — toggle sources on/off

---

## Phase 3: Wake Word Detection
**Goal:** "Hey Jarvis" activates listening without button press.

| Component | File | Description |
|---|---|---|
| Voice Session | `backend/app/services/voice_session_service.py` | Per-connection `VoiceSession` state machine (LISTENING → COMMAND → THINKING → SPEAKING) owns the full streaming voice loop |
| Wake Word Detection | openWakeWord inside VoiceSession | `hey_jarvis` scored frame-by-frame (1280 samples/80ms) on the continuous 16kHz s16 PCM stream |
| VAD | openwakeword.vad.VAD (silero_vad.onnx) | Command endpointing: 480-sample chunks, onset/offset counters |
| Activation Pipeline | `backend/app/routers/websocket.py` | `audio_frame` frames feed the session; detection → STT → command pipeline → TTS → `voice_response` |
| Barge-in | VoiceSession | Wake re-detection during SPEAKING interrupts playback; wake word required every turn |

**New command handlers:**
- `voice_mode_start` — start the streaming voice session
- `audio_frame` — stream raw s16 PCM frames
- `tts_done` — TTS playback finished → back to listening
- `voice_mode_stop` — tear down the session
- `wake_word_config` — sensitivity, wake phrase

---

## Phase 4: Task Automation & Routines
**Goal:** Multi-step voice commands with progress feedback.

| Component | File | Description |
|---|---|---|
| Routine Service | `backend/app/services/routine_service.py` | Define/execute named routines (JSON stored) |
| Built-in Routines | Inside routine_service.py | "good night", "i'm leaving", "work mode", "movie time" |
| Custom Routines | User-defined via voice | "create a routine called X that does Y, Z" |
| Progress Tracking | WebSocket events | `routine_progress` as each step completes |

**Built-in routines:**
- **Good night** → lock PC, dim lights, set do-not-disturb
- **I'm leaving** → shutdown services, lock PC, turn off lights
- **Work mode** → open specific apps, set volume, enable focus lights
- **Movie time** → dim lights, open media app, set volume

**New command handlers:**
- `create_routine` — define new routine
- `run_routine` — execute routine
- `list_routines` — show available routines
- `delete_routine` — remove routine

---

## Phase 5: Contextual Awareness & Email
**Goal:** Jarvis knows what you're doing and keeps you updated on email.

| Component | File | Description |
|---|---|---|
| Screen Context Tracker | `backend/app/services/screen_context_service.py` | Periodic OCR screenshots → summarize what's on screen |
| Context Memory | SQLite | Store last N screen summaries for recall |
| Gmail Integration | `backend/app/services/email_service.py` | OAuth2 → google-api-python-client — read/summarize/archive |
| Notification Monitor | `backend/app/services/notification_service.py` | Watch Windows toast notifications via UI Automation |

**New command handlers:**
- `screen_context` — what's currently on screen
- `check_email` — check for new emails
- `email_summary` — summarize recent emails
- `get_notifications` — recent notifications

---

## Phase 6: Proactive Suggestions
**Goal:** Jarvis makes unsolicited helpful observations.

| Component | File | Description |
|---|---|---|
| Suggestion Engine | `backend/app/services/suggestion_engine.py` | Rule-based + pattern-based suggestion generator |
| Time Patterns | Inside suggestion_engine.py | "You usually open VS Code at this time" — learns from activity log |
| System Suggestions | Rules | "Your disk is 95% full, shall I clean temp files?" |
| Wellness Suggestions | Rules | "You've been working for 2 hours, take a break?" |
| Context Suggestions | Rules | "I see you're reading a PDF, shall I summarize it?" |
| Cooldown | 1 suggestion per 15 min max | Avoids annoyance |

**New command handlers:**
- `get_suggestions` — current suggestions
- `dismiss_suggestion` — dismiss a suggestion
- `set_suggestion_rules` — configure suggestion behavior

---

## Phase 7: TTS Personality & Jarvis Wit
**Goal:** Responses sound like the real JARVIS — dry, British, occasionally witty.

| Component | File | Description |
|---|---|---|
| Personality Enhancer | `backend/app/services/personality_enhancer.py` | Post-processes LLM responses to add Jarvis flair |
| British Wit Library | Inside personality_enhancer.py | Curated quips, dry observations, understated humor |
| Contextual Remarks | Unsolicited | "Interesting code, sir" / "Bold choice of variable names" |
| Status Readouts | "All systems nominal" / "Running like a Swiss watch" |
| Config Toggle | personality_service.py | Formal ↔ playful slider, quip frequency |

No new handlers — enhances existing `personality_service`.

---

## Phase 8: Multi-Device Orchestration
**Goal:** Jarvis reaches across all your devices.

| Component | File | Description |
|---|---|---|
| Device Mesh | `backend/app/services/device_mesh_service.py` | WebSocket mesh — PC ↔ phone ↔ wearable relay messages |
| Push to Phone | WebSocket relay | Send text/files/links to phone |
| Cross-device Clipboard | Clipboard sync | Sync clipboard content between devices |
| File Transfer | WebSocket chunked | "Send this file to my phone" |
| Remote Commands | Authenticated | Phone can trigger PC commands |

**New command handlers:**
- `send_to_device` — push content to specific device
- `sync_clipboard` — sync clipboard between devices
- `transfer_file` — send file to another device
- `remote_command` — execute command on another device

---

## New Dependencies
```
feedparser              # RSS news
google-api-python-client # Gmail/Calendar
google-auth-oauthlib    # OAuth flow
webrtcvad               # Voice activity detection
psutil                  # System monitoring
GPUtil                  # GPU temperature
```

## New Flutter Screens/Widgets
- Briefing screen — morning readout display
- Monitoring dashboard — live system stats
- Routine manager — create/edit/run routines
- Notification center — email + system notifications
- Suggestion toast — proactive suggestion popups

---

## Build Order
```
Phase 1 (Monitoring)      ~3 days
Phase 2 (Briefing)        ~3 days
Phase 3 (Wake Word)       ~4 days
Phase 4 (Routines)        ~3 days
Phase 5 (Email/Context)   ~4 days
Phase 6 (Suggestions)     ~2 days
Phase 7 (TTS Personality) ~1 day
Phase 8 (Multi-Device)    ~4 days
                          ─────────
                          ~24 days
```

---

## Related

- [[AGENTS]] — project rules
- [[ROADMAP]] — project timeline
- [[DATA_STRUCTURE]] — data models
- [[SETUP]] — installation guide
- [[API_DOCS]] — API reference
- [[Memory Map]] — vault index
