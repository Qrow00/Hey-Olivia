# J.A.R.V.I.S. Backend API

## Quick Start

### Prerequisites
- Python 3.10+
- Ollama (for LLM)
- FFmpeg (for audio processing)

### Installation

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Development
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify

```bash
# Health check
curl http://localhost:8000/

# API info
curl http://localhost:8000/api/v1
```

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### WebSocket
```
ws://localhost:8000/ws
```

---

## Endpoints

### Devices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices` | List all devices |
| POST | `/api/v1/devices` | Register a device |
| GET | `/api/v1/devices/{id}` | Get device details |
| PUT | `/api/v1/devices/{id}` | Update device |
| DELETE | `/api/v1/devices/{id}` | Remove device |

### Cameras (RTSP)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cameras` | List all cameras |
| POST | `/api/v1/cameras` | Add a camera |
| GET | `/api/v1/cameras/{id}` | Get camera details |
| DELETE | `/api/v1/cameras/{id}` | Remove camera |
| POST | `/api/v1/cameras/{id}/stream/start` | Start stream |
| POST | `/api/v1/cameras/{id}/stream/stop` | Stop stream |
| POST | `/api/v1/cameras/{id}/snapshot` | Take snapshot |

### Wearables (Health)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/wearables` | List wearables |
| POST | `/api/v1/wearables` | Register wearable |
| GET | `/api/v1/wearables/{id}` | Get wearable details |
| DELETE | `/api/v1/wearables/{id}` | Remove wearable |
| POST | `/api/v1/wearables/{id}/health` | Record health data |
| GET | `/api/v1/wearables/{id}/health` | Get health summary |
| GET | `/api/v1/wearables/{id}/health/history` | Get health history |

### Smart Home
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/smart-home` | List devices |
| POST | `/api/v1/smart-home` | Add device |
| DELETE | `/api/v1/smart-home/{id}` | Remove device |
| POST | `/api/v1/smart-home/{id}/control` | Control device |
| POST | `/api/v1/smart-home/{id}/on` | Turn on |
| POST | `/api/v1/smart-home/{id}/off` | Turn off |
| POST | `/api/v1/smart-home/{id}/toggle` | Toggle |
| POST | `/api/v1/smart-home/{id}/brightness` | Set brightness |
| POST | `/api/v1/smart-home/{id}/color` | Set color |
| POST | `/api/v1/smart-home/mqtt/connect` | Connect MQTT |

### Vision (AI)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/vision/analyze` | Analyze camera feed |
| POST | `/api/v1/vision/quick-look/{camera_id}` | Quick camera look |
| POST | `/api/v1/vision/scan-all` | Scan all cameras |
| POST | `/api/v1/vision/observe/start` | Start observation |
| POST | `/api/v1/vision/observe/stop/{session_id}` | Stop observation |
| GET | `/api/v1/vision/observe/sessions` | List observation sessions |

### Commands
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/commands` | List all commands |
| POST | `/api/v1/commands/parse` | Parse a command |
| POST | `/api/v1/commands/execute` | Execute a command |

### Plugins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/plugins` | List all plugins |
| GET | `/api/v1/plugins/capabilities` | List capabilities |
| GET | `/api/v1/plugins/{id}` | Get plugin details |
| POST | `/api/v1/plugins/{id}/enable` | Enable plugin |
| POST | `/api/v1/plugins/{id}/disable` | Disable plugin |
| POST | `/api/v1/plugins/command` | Execute plugin command |

### Voice
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/voice/stt` | Speech to text |
| POST | `/api/v1/voice/tts` | Text to speech |
| POST | `/api/v1/voice/chat` | Chat completion |

### Screen Share
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/screen/sessions` | List sessions |
| POST | `/api/v1/screen/analyze` | Analyze screen |

### Conversations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/conversations?user_id={id}` | List user conversations |
| GET | `/api/v1/conversations/{id}` | Get conversation messages |

### Voice Profiles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/voice-profiles` | List all profiles |
| GET | `/api/v1/voice-profiles/active` | Get active profile |
| POST | `/api/v1/voice-profiles/active` | Set active profile |
| POST | `/api/v1/voice-profiles` | Create profile |
| PUT | `/api/v1/voice-profiles/{id}` | Update profile |
| DELETE | `/api/v1/voice-profiles/{id}` | Delete profile |
| GET | `/api/v1/voice-profiles/{id}/tts-config` | Get edge-tts config |

### Personality
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/personality` | Get personality status |
| GET | `/api/v1/personality/prompt` | Get system prompt |
| POST | `/api/v1/personality/style` | Update style traits |
| POST | `/api/v1/personality/opinion` | Learn opinion |
| POST | `/api/v1/personality/preference` | Learn preference |
| POST | `/api/v1/personality/feedback` | Adjust from feedback |
| POST | `/api/v1/personality/name` | Set preferred name |
| GET | `/api/v1/personality/opinions` | List learned opinions |
| GET | `/api/v1/personality/reflections` | List reflections |

### Browser (Hermes)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/browser/sessions` | Create browser session |
| DELETE | `/api/v1/browser/sessions/{id}` | Destroy session |
| GET | `/api/v1/browser/sessions` | List sessions |
| GET | `/api/v1/browser/sessions/{id}` | Get session info |
| POST | `/api/v1/browser/navigate` | Navigate to URL |
| POST | `/api/v1/browser/click` | Click element |
| POST | `/api/v1/browser/type` | Type text |
| GET | `/api/v1/browser/screenshot/{id}` | Take screenshot |
| GET | `/api/v1/browser/snapshot/{id}` | Get page snapshot |
| POST | `/api/v1/browser/extract` | Extract content |
| POST | `/api/v1/browser/scroll` | Scroll page |
| POST | `/api/v1/browser/back` | Go back |
| POST | `/api/v1/browser/forward` | Go forward |
| POST | `/api/v1/browser/search` | Google search |

---

## WebSocket Events

### Client → Server
| Event | Description |
|-------|-------------|
| `ping` | Keepalive |
| `voice_chunk` | Send audio for STT |
| `text_message` | Send text message |
| `device_register` | Register device |
| `device_heartbeat` | Device heartbeat |
| `camera_view` | View camera feed |
| `vision_analyze` | Analyze camera |
| `vision_quick_look` | Quick camera look |
| `vision_observe_start` | Start observation |
| `wearable_health_update` | Health data update |
| **Monitoring** | |
| `monitoring_snapshot` | Get current system metrics |
| `monitoring_history` | Get metrics history (params: `minutes`) |
| `monitoring_alerts` | Get alert history (params: `limit`) |
| `monitoring_thresholds` | Get alert thresholds |
| `monitoring_set_threshold` | Set threshold (params: `metric`, `value`) |
| `activity_log` | Get activity log (params: `limit`) |
| `activity_window` | Get active window history (params: `minutes`) |
| `activity_processes` | Get top processes |
| **Briefing** | |
| `morning_briefing` | Generate morning briefing (params: `include_tts`) |
| `briefing_config` | Update briefing sources (params: `sources`) |
| **Wake Word** | |
| `wake_word_start` | Start wake word detection |
| `wake_word_stop` | Stop wake word detection |
| `wake_word_config` | Update config (params: `phrases`, `sensitivity`) |
| **Routines** | |
| `run_routine` | Run a routine (params: `name`) |
| `create_routine` | Create routine (params: `name`, `description`, `steps`, `trigger_phrase`) |
| `list_routines` | List all routines |
| `delete_routine` | Delete routine (params: `name`) |
| **Email & Context** | |
| `check_email` | Check recent emails (params: `limit`, `query`) |
| `email_summary` | Summarize emails (params: `limit`) |
| `screen_context` | Capture and summarize screen |
| `get_notifications` | Get recent notifications |
| **Suggestions** | |
| `get_suggestions` | Get proactive suggestions |
| `dismiss_suggestion` | Dismiss suggestion (params: `suggestion_id`) |
| **Personality** | |
| `personality_enhance` | Enhance response text (params: `text`, `context`) |
| `personality_config` | Update personality (params: `setting`, `value`) |
| **Device Mesh** | |
| `mesh_register` | Register on device mesh |
| `mesh_heartbeat` | Device mesh heartbeat |
| `push_to_device` | Send message to device (params: `device_id`, `content`) |
| `clipboard_sync` | Sync clipboard |
| `transfer_file` | Start file transfer (params: `file_path`, `target_device`) |
| `transfer_chunk` | Send file chunk |
| `mesh_devices` | List mesh devices |
| **Browser** | |
| `browser_create_session` | Create browser session |
| `browser_destroy_session` | Destroy browser session |
| `browser_navigate` | Navigate to URL |
| `browser_click` | Click element |
| `browser_type` | Type text |
| `browser_screenshot` | Take screenshot |
| `browser_snapshot` | Get page snapshot |
| `browser_scroll` | Scroll page |
| `browser_search` | Google search |
| `browser_get_state` | Get browser state |
| `browser_new_tab` | Open new tab |
| `browser_switch_tab` | Switch tab |
| `browser_close_tab` | Close tab |
| `browser_page_summary` | Get page summary |
| **RAG & OCR** | |
| `rag_ingest` | Ingest text or file (params: `text`, `file_path`, `source`) |
| `rag_search` | Search knowledge base (params: `query`, `top_k`) |
| `rag_status` | Get RAG stats |
| `ocr_image` | OCR an image (params: `image`, `prompt`, `mode`) |
| `ocr_screenshot` | OCR current screen (params: `prompt`) |

### Server → Client
| Event | Description |
|-------|-------------|
| `pong` | Keepalive response |
| `avatar_state` | Avatar state change |
| `voice_response` | Voice response with audio |
| `text_response` | Text response |
| `command_response` | Command execution result |
| `camera_frame` | Camera frame data |
| `vision_result` | AI vision analysis |
| `vision_observation` | Observation update |
| `vision_alert` | Security alert |
| `wearable_health_data` | Health metric update |
| **Monitoring** | |
| `monitoring_snapshot` | System metrics snapshot |
| `monitoring_history` | Metrics history data |
| `monitoring_alerts` | Alert history |
| `monitoring_thresholds` | Current thresholds |
| `monitoring_threshold_set` | Threshold updated confirmation |
| `activity_log` | Activity log entries |
| `activity_window_history` | Active window history |
| `activity_processes` | Top processes |
| **Briefing** | |
| `briefing_status` | Briefing generation status |
| `briefing_result` | Generated briefing data |
| `briefing_config` | Current briefing config |
| **Wake Word** | |
| `wake_word_detected` | Wake word phrase detected |
| `wake_word_result` | Start/stop result |
| `wake_word_config` | Current wake word config |
| **Routines** | |
| `routine_started` | Routine execution started |
| `routine_progress` | Routine step progress |
| `routine_result` | Routine execution result |
| `routine_created` | Routine creation result |
| `routine_list` | List of routines |
| `routine_deleted` | Deletion result |
| **Email & Context** | |
| `email_list` | Recent emails |
| `email_summary` | Email summary |
| `screen_context_result` | Screen capture analysis |
| `notification_list` | Recent notifications |
| **Suggestions** | |
| `suggestion_list` | Proactive suggestions |
| `suggestion_dismissed` | Dismissal confirmation |
| **Personality** | |
| `personality_enhanced` | Enhanced response text |
| `personality_config` | Current personality config |
| **Device Mesh** | |
| `mesh_registered` | Mesh registration result |
| `mesh_heartbeat_ack` | Mesh heartbeat ack |
| `push_message_received` | Message from another device |
| `clipboard_data` | Clipboard content |
| `transfer_started` | File transfer started |
| `transfer_progress` | File transfer progress |
| `transfer_complete` | File transfer complete |
| `mesh_device_list` | List of mesh devices |
| **Browser** | |
| `browser_session_created` | Session created |
| `browser_session_destroyed` | Session destroyed |
| `browser_navigating` | Navigation started |
| `browser_navigate_result` | Navigation result |
| `browser_click_result` | Click result |
| `browser_type_result` | Type result |
| `browser_screenshot` | Screenshot data |
| `browser_snapshot` | Page snapshot |
| `browser_scroll_result` | Scroll result |
| `browser_searching` | Search started |
| `browser_search_result` | Search result |
| `browser_state` | Browser state |
| `browser_new_tab_result` | New tab result |
| `browser_switch_tab_result` | Tab switch result |
| `browser_close_tab_result` | Tab close result |
| `browser_page_summary` | Page content summary |
| **RAG & OCR** | |
| `rag_ingest_result` | Ingest result |
| `rag_search_result` | Search results |
| `rag_status` | RAG stats |
| `ocr_processing` | OCR processing status |
| `ocr_result` | OCR extraction result |

---

## Voice Commands

| Category | Commands |
|----------|----------|
| **System** | "what time", "what date", "remind me to..." |
| **Smart Home** | "turn on/off lights", "set brightness", "lock door" |
| **Camera** | "show cameras", "take photo", "look at camera" |
| **Vision** | "what do you see", "scan cameras", "watch camera" |
| **Health** | "heart rate", "blood oxygen", "steps today" |
| **Screen** | "share screen", "stop screen share" |
| **Media** | "play music", "stop music" |
| **Info** | "weather in...", "search for..." |
| **Monitoring** | "system health", "get alerts", "activity log", "active window", "top processes" |
| **Briefing** | "morning briefing", "briefing config" |
| **Wake Word** | "start listening", "stop listening", "wake word config" |
| **Routines** | "run routine", "create routine", "list routines", "delete routine" |
| **Email** | "check email", "email summary" |
| **Context** | "screen context", "get notifications" |
| **Suggestions** | "get suggestions", "dismiss suggestion" |
| **Personality** | "personality config", "set formality", "set quip frequency" |
| **Device Mesh** | "send to device", "sync clipboard", "transfer file" |
| **Knowledge** | "knowledge summary", "knowledge search", "learn this" |
| **RAG** | "search knowledge", "ingest text", "rag status", "clear knowledge" |
| **OCR** | "read screen", "ocr file" |

---

## Related

- [[AGENTS]] — project rules
- [[ROADMAP]] — project timeline
- [[DATA_STRUCTURE]] — data models
- [[SETUP]] — installation guide
- [[JARVIS_ENHANCEMENT_PLAN]] — future features
- [[Memory Map]] — vault index
