# Project Memory

## Project: J.A.R.V.I.S.
- **Path:** `C:\Users\toshi\Documents\main jarvis`
- **Description:** Personal AI Assistant
- **Type:** TypeScript/Node.js (ESM) + FastAPI (Python) + Flutter (Dart)

## Obsidian Vault
- **Location:** `C:\Users\toshi\Documents\main jarvis\vault`
- **Created:** 2026-07-18

## Roadmap
- **Location:** `vault/ROADMAP.md`
- **Timeline:** 1-2 months MVP
- **Platform:** Flutter (Android, Windows, Linux)
- **Backend:** FastAPI (Python) on HP EliteDesk
- **Current Phase:** Phase 2 — Core Voice (Week 3-4)
- **Completed:** Phase 1 — Foundation ✅

## Project Structure
- `.obsidian/` — Original Obsidian config (root level)
- `vault/` — Separate Obsidian vault for documentation/notes
- `types/` — TypeScript type definitions (all 10 data structures complete)
  - `user.ts`, `device.ts`, `conversation.ts`, `avatar.ts`, `voice.ts`
  - `screen.ts`, `command.ts`, `app.ts`, `api.ts`, `database.ts`
- `backend/` — FastAPI (Python) server
  - `app/main.py` — FastAPI app entry
  - `app/models/` — SQLAlchemy models (User, Device, Conversation, Message, Command)
  - `app/routers/` — REST endpoints + WebSocket hub
  - `requirements.txt` — Python dependencies
- `client/` — Flutter app (Android, Windows, Linux)
  - `lib/main.dart` — App entry with bottom nav
  - `lib/screens/` — HomeScreen, DevicesScreen, SettingsScreen
  - `lib/widgets/` — AvatarWidget (animated), DeviceCard
  - `lib/services/` — WebSocketService, ApiService
  - `lib/models/` — Device, Conversation models
- `run-backend.ps1` — Start backend server
- `run-client.ps1` — Start Flutter client
- `DATA_STRUCTURE.md` — Data structure documentation
- `jarvis-avatar-preview.html` — Avatar preview file

## Run Commands
- Backend: `.\run-backend.ps1` or `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Client: `.\run-client.ps1` or `flutter run -d windows`
- Flutter path: `C:\flutter\bin` (add to PATH)

## Recent Changes
- 2026-07-18: Added `types/database.ts` (DBUser, DBDevice, DBConversation, DBMessage, DBCommand)
- 2026-07-18: Created Obsidian vault at `vault/`
- 2026-07-18: Created MVP roadmap at `vault/ROADMAP.md`
- 2026-07-18: Phase 1 Complete — Backend (FastAPI) + Client (Flutter) initialized
  - Installed Flutter SDK at `C:\flutter`
  - Created FastAPI backend with SQLAlchemy models + WebSocket
  - Created Flutter client with screens, widgets, services
  - Backend tested and running on port 8000
