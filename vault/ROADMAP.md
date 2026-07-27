# J.A.R.V.I.S. MVP Roadmap (1-2 Months)

## Platform: Flutter
- Android phone/tablet ✅
- Windows desktop ✅
- Linux desktop ✅
- Single codebase, good performance, strong community

---

## Phase 1: Foundation (Week 1-2) ✅ DONE
| Task | Details |
|------|---------|
| ~~Project setup~~ | ~~Flutter app, FastAPI backend, project structure~~ |
| ~~Tailscale networking~~ | ~~Device discovery, WebSocket connection~~ |
| ~~Database setup~~ | ~~SQLite/Realm local + server DB schemas~~ |
| Auth flow | Simple token-based device pairing |

## Phase 2: Core Voice (Week 3-4) ✅ DONE
| Task | Details |
|------|---------|
| ~~STT integration~~ | ~~Whisper on server (base model)~~ |
| ~~TTS integration~~ | ~~Edge-TTS with voice selection~~ |
| ~~LLM integration~~ | ~~Ollama (llama3.2)~~ |
| ~~WebSocket pipeline~~ | ~~Real-time voice streaming with avatar sync~~ |
| ~~Avatar state sync~~ | ~~5-state visual system with animations~~ |

## Phase 3: Device Management (Week 5-6) ✅ DONE
| Task | Details |
|------|---------|
| ~~Device registry~~ | ~~Add/remove/view devices with CRUD API~~ |
| ~~Status monitoring~~ | ~~Online/offline, battery, signal, heartbeat~~ |
| ~~Capabilities detection~~ | ~~Auto-discover device features by platform~~ |
| ~~Multi-device dashboard~~ | ~~Real-time UI with filters, stats, actions~~ |

## Phase 4: Screen Sharing (Week 7-8) ✅ DONE
| Task | Details |
|------|---------|
| ~~Screen capture~~ | ~~Flutter platform channel for native capture~~ |
| ~~WebSocket streaming~~ | ~~JPEG frames over WS with session management~~ |
| ~~Basic analysis~~ | ~~LLM-powered screen analysis endpoint~~ |
| ~~Remote view~~ | ~~Full viewer UI with fullscreen, viewer count, live indicator~~ |

## Phase 5: Smart Home & Polish (Week 9-10) ✅ DONE
| Task | Details |
|------|---------|
| ~~RTSP integration~~ | ~~CCTV camera feeds with live streaming~~ |
| ~~Wearable support~~ | ~~Heart rate, SpO2, sleep, steps, calories, stress, temperature~~ |
| ~~Smart home control~~ | ~~MQTT/HTTP/Tasmota/Shelly device control with scenes~~ |
| ~~Command registry~~ | ~~Voice command parsing with regex patterns~~ |
| ~~UI polish~~ | ~~Settings, notifications, error handling~~ |

## Phase 6: Future Proofing (Week 11-12) ✅ DONE
| Task | Details |
|------|---------|
| ~~Plugin system~~ | ~~Abstract DevicePlugin base, PluginManager, motion detector plugin~~ |
| ~~API versioning~~ | ~~All endpoints under /api/v1/ prefix~~ |
| ~~Documentation~~ | ~~SETUP.md, API_DOCS.md~~ |
| ~~Testing~~ | ~~17 tests passing (API, commands, plugins)~~ |

---

## Architecture Overview

```
+-------------------------------------------+
|           FLUTTER APP (Client)            |
|  Android / Windows / Linux                |
|  +---------+ +----------+ +---------+     |
|  | Avatar  | |  Voice   | | Screen  |     |
|  |   UI    | | Pipeline | |  Share  |     |
|  +----+----+ +----+-----+ +----+----+     |
|       +-----------+-----------+           |
|                   | WebSocket             |
+-------------------+-----------------------+
                    |
+-------------------+-----------------------+
|      HP ELITEDESK (FastAPI Server)        |
|  +---------+ +----------+ +---------+     |
|  | Ollama  | | Whisper  | |  Piper  |     |
|  |  (LLM)  | |  (STT)   | |  (TTS)  |     |
|  +---------+ +----------+ +---------+     |
|  +---------+ +----------+ +---------+     |
|  |  ADB    | |   SSH    | |  RTSP   |     |
|  | (Phone) | |   (PC)   | | (CCTV)  |     |
|  +---------+ +----------+ +---------+     |
+-------------------------------------------+
```

---

## Tech Stack
- **Client:** Flutter (Dart)
- **Server:** FastAPI (Python)
- **AI:** Ollama (llama3.2, llava:7b)
- **Voice:** Whisper/Vosk (STT), Piper/Edge-TTS (TTS)
- **Networking:** Tailscale
- **Protocol:** WebSocket (real-time), REST (config)
- **Database:** SQLite/Realm (local), PostgreSQL (server)

---

## Related

- [[AGENTS]] — project rules and architecture
- [[DATA_STRUCTURE]] — data models and schemas
- [[SETUP]] — installation and configuration
- [[API_DOCS]] — backend API reference
- [[JARVIS_ENHANCEMENT_PLAN]] — future feature roadmap
- [[Memory Map]] — vault index
