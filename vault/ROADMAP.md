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

## Phase 2: Core Voice (Week 3-4)
| Task | Details |
|------|---------|
| STT integration | Whisper/Vosk on server |
| TTS integration | Piper/Edge-TTS |
| LLM integration | Ollama (llama3.2) |
| WebSocket pipeline | Real-time voice streaming |
| Avatar state sync | Voice → avatar animation |

## Phase 3: Device Management (Week 5-6)
| Task | Details |
|------|---------|
| Device registry | Add/remove/view devices |
| Status monitoring | Online/offline, battery, signal |
| Capabilities detection | Auto-discover device features |
| Multi-device dashboard | UI for all connected devices |

## Phase 4: Screen Sharing (Week 7-8)
| Task | Details |
|------|---------|
| Screen capture | Android (MediaProjection), Desktop (FFmpeg/GDI) |
| WebSocket streaming | JPEG frames over WS |
| Basic analysis | OCR, object detection (optional) |
| Remote view | View device screens from any client |

## Phase 5: Smart Home & Polish (Week 9-10)
| Task | Details |
|------|---------|
| RTSP integration | CCTV camera feeds |
| Light control | MQTT/HTTP device control |
| Command registry | Voice commands for home devices |
| UI polish | Settings, error handling, notifications |

## Phase 6: Future Proofing (Week 11-12)
| Task | Details |
|------|---------|
| Plugin system | Device capability plugins |
| API versioning | v1 endpoint structure |
| Documentation | Setup guide, API docs |
| Testing | Unit + integration tests |

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
