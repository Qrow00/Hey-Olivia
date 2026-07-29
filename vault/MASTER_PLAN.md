# J.A.R.V.I.S. Master Plan — Multi-Device Architecture

## Architecture Overview

```
                    ┌──────────────────────┐
                    │  JARVIS SERVER        │
                    │  HP EliteDesk          │
                    │  FastAPI + Ollama       │
                    │                        │
                    │  services/              │
                    │  ├── settings_service   │── stores all prefs in SQLite
                    │  ├── tailscale_service  │── detects Tailscale IP
                    │  └── wearable_service   │── persists to DB
                    │                        │
                    │  adds to greeting:      │── sends settings + tailscale IP
                    │  on WebSocket connect    │   on first connection
                    └────────┬───────────────┘
                             │ Tailscale
              ┌──────────────┼────────────────┐
              │              │                 │
    ┌─────────▼──────┐ ┌────▼────────┐ ┌──────▼────────┐
    │ DESKTOP CLIENT  │ │ PHONE        │ │ TABLET         │
    │ Flutter         │ │ Flutter      │ │ Flutter        │
    │                 │ │              │ │                │
    │ Overlay window  │ │ HealthBridge │ │ Wearable view  │
    │ (always-on-top) │ │ → reads from │ │ (fetches from  │
    │ Main app window │ │   HealthKit / │ │  server)       │
    │                 │ │   HealthConn. │ │                │
    │ Settings UI     │ │ → relays to  │ │ Settings UI    │
    │ reads from      │ │   server via │ │ reads from     │
    │ server via API  │ │   WebSocket  │ │ server via API │
    └─────────────────┘ └──────────────┘ └────────────────┘
```

## Phase 0: Server Foundation

### 0a — Settings Service (`backend/app/services/settings_service.py`) **NEW**

Stores all user preferences in `settings.json` (simple file, no DB migration needed).

| Method | Description |
|--------|-------------|
| `get_all()` | Returns full settings dict |
| `update(partial)` | Merges partial updates |
| `reset()` | Returns to defaults |

Settings schema:
```python
{
    "voice": {
        "wake_word_enabled": True,
        "wake_word_sensitivity": 0.5,
        "tts_voice": "en-US-GuyNeural",
        "voice_profile": "jarvis",
        "llm_model": "llama3.2",
        "push_to_talk": False
    },
    "ui": {
        "dark_mode": True,
        "notifications_enabled": True
    },
    "health": {
        "alerts_enabled": False,
        "heart_rate_alerts": True,
        "spo2_alerts": True
    },
    "smart_home": {
        "mqtt_broker": "",
        "mqtt_port": 1883,
        "mqtt_username": "",
        "mqtt_password": ""
    }
}
```

### 0b — Update Settings Router (`backend/app/routers/settings.py`) **MODIFY**

| Method | Path | Current | After |
|--------|------|---------|-------|
| `GET /` | `/api/v1/settings` | Returns `{"theme": "dark"}` hardcoded | Returns `settings_service.get_all()` |
| `PUT /` | `/api/v1/settings` | Returns `{"status": "updated"}` | Calls `settings_service.update()` |
| `PATCH /` | `/api/v1/settings` | — | **New:** partial update |

### 0c — Welcome Endpoint (`backend/app/routers/system.py`) **MODIFY**

Add `GET /api/v1/system/welcome`:
```json
{
    "version": "2.0.0",
    "hostname": "elitedesk",
    "services": ["voice", "monitoring", "browser"],
    "tailscale": {
        "available": true,
        "ip": "100.64.23.45"
    },
    "settings": { ... }
}
```

### 0d — Tailscale Service (`backend/app/services/tailscale_service.py`) **NEW**

```python
class TailscaleService:
    def detect_ip() -> Optional[str]:
        # runs: tailscale ip -4
        # caches result, refreshes every 60s

    def is_available() -> bool:
        # checks if tailscale CLI exists and status is running
```

Exposes: `GET /api/v1/system/tailscale` → `{ "ip": "100.x.x.x", "available": true }`

### 0e — Inject Settings + Tailscale into WebSocket Greeting **MODIFY**

In `send_greeting()`, add to welcome message:
```json
{
    "type": "welcome",
    "settings": { ... },
    "tailscale": { ... }
}
```

## Phase 1: Client Foundation

### 1a — server_config.dart (`client/lib/services/server_config.dart`) **NEW**

Stores only what the client needs to reach the server. Persisted to `server_config.json` via `path_provider`.

```dart
class ServerConfig {
    static ServerConfig? _instance;
    String baseUrl;        // http://100.x.x.x:8000
    String wsUrl;          // ws://100.x.x.x:8000/ws
    String? tailscaleIp;   // cached from onboarding

    static Future<ServerConfig> load();
    Future<void> save();
    static Future<bool> testConnection(String url);
    static Future<String?> discoverViaTailscan();
}
```

Resolution chain:
1. Try saved `baseUrl` → if works, done
2. Try cached `tailscaleIp` → if works, save and done
3. Return null → manual entry

### 1b — settings_service.dart (`client/lib/services/settings_service.dart`) **NEW**

```dart
class SettingsService {
    Map<String, dynamic> _settings = {};
    Future<void> fetch();     // GET /api/v1/settings
    Future<void> save();      // PUT /api/v1/settings
    Future<void> patch();     // PATCH /api/v1/settings
    // typed getters with defaults
}
```

## Phase 2: Onboarding

### 2a — onboarding_screen.dart (`client/lib/screens/onboarding_screen.dart`) **NEW**

3-step wizard with swipeable PageView:
- **Step 1: Welcome** — Avatar animation, branding, [Get Started]
- **Step 2: Connect** — Server URL field, [Test Connection], shows server info
- **Step 3: Complete** — Fetches settings, saves URL, enters main app

### 2b — Update main.dart **MODIFY**

- First launch → OnboardingScreen
- Subsequent → try `ServerConfig.resolve()` → success → JarvisMainScreen | fail → OnboardingScreen step 2

### 2c — Demote SpecsCheckScreen **MODIFY**

Move to Settings → System Info. Hardware scan runs silently in background after onboarding.

## Phase 3: Settings Screen Wired

### 3a — Update settings_screen.dart **MODIFY**

Wire every field to `SettingsService.patch()`. Remove server URL field (belongs in onboarding).

## Phase 4: Desktop Overlay

### 4a — Add `window_manager` to pubspec.yaml

```yaml
dependencies:
  window_manager: ^0.4.0
```

### 4b — overlay_widget.dart (`client/lib/overlay/overlay_widget.dart`) **NEW**

Frameless always-on-top window (~200x300) with:
- Compact avatar (reduced custom painter)
- Health bar (heart rate, SpO2, steps from WS)
- Mic controls (PTT, wake word toggle)
- Right-click menu: Show Main, Settings, Quit
- Draggable via title bar

### 4c — Window manager in main.dart **MODIFY**

Desktop: overlay stays on top independently of main window.

### 4d — compact_avatar_widget.dart (`client/lib/widgets/compact_avatar_widget.dart`) **NEW**

Simplified avatar: ~120x120, core rings + center dot, same state colors.

## Phase 5: Mobile Wearable Bridge

### 5a — HealthBridgePlugin.kt **NEW**

```kotlin
MethodChannel("health_bridge")
    // isAvailable, requestPermissions, readMetrics, startObserving, stopObserving
```

Android: Health Connect API (`androidx.health.connect:connect-client:1.1.0`)
Permissions: `HEART_RATE`, `OXYGEN_SATURATION`, `STEPS`, `SLEEP`, `CALORIES_BURNED`, `STRESS`

### 5b — Register in MainActivity.kt **MODIFY**

Add `"health_bridge"` channel alongside `"screen_capture"`.

### 5c — HealthBridgePlugin.swift **NEW**

iOS: HealthKit API via `HKHealthStore`.

### 5d — health_bridge_service.dart (`client/lib/services/health_bridge_service.dart`) **NEW**

```dart
class HealthBridgeService {
    static const MethodChannel _channel = MethodChannel('health_bridge');
    void startPolling(WearableService ws, String deviceId) {
        // Every 5s: readMetrics() → ws.updateHealth() → server
    }
}
```

### 5e — Auto-register Phone as Wearable Source **MODIFY**

On device_register with type "phone" → server auto-creates WearableDevice → phone starts health bridge.

## Phase 6: Server Wearable Persistence

### 6a — Migrate to SQLite **MODIFY**

Add `WearableDeviceDB` and `HealthMetricDB` tables to `models.py`.
Update `WearableService` to read/write SQLite instead of in-memory dicts.

## File Change Summary

| # | File | Phase |
|---|------|-------|
| 1 | `backend/app/services/settings_service.py` | 0a |
| 2 | `backend/app/services/tailscale_service.py` | 0d |
| 3 | `backend/app/routers/settings.py` | 0b |
| 4 | `backend/app/routers/system.py` | 0c |
| 5 | `backend/app/routers/websocket.py` | 0e |
| 6 | `backend/app/main.py` | 0 |
| 7 | `client/lib/services/server_config.dart` | 1a |
| 8 | `client/lib/services/settings_service.dart` | 1b |
| 9 | `client/lib/screens/onboarding_screen.dart` | 2a |
| 10 | `client/lib/main.dart` | 2b |
| 11 | `client/lib/screens/specs_check_screen.dart` | 2c |
| 12 | `client/lib/screens/settings_screen.dart` | 3a |
| 13 | `client/pubspec.yaml` | 4a |
| 14 | `client/lib/overlay/overlay_widget.dart` | 4b |
| 15 | `client/lib/overlay/overlay_manager.dart` | 4c |
| 16 | `client/lib/widgets/compact_avatar_widget.dart` | 4d |
| 17 | `client/android/.../HealthBridgePlugin.kt` | 5a |
| 18 | `client/android/app/build.gradle.kts` | 5a |
| 19 | `client/android/.../AndroidManifest.xml` | 5a |
| 20 | `client/android/.../MainActivity.kt` | 5b |
| 21 | `client/ios/.../HealthBridgePlugin.swift` | 5a |
| 22 | `client/ios/Runner/Info.plist` | 5a |
| 23 | `client/lib/services/health_bridge_service.dart` | 5d |
| 24 | `client/lib/services/wearable_service.dart` | 5e |
| 25 | `backend/app/services/wearable_service.py` | 6a |
| 26 | `backend/app/models/models.py` | 6a |
| 27 | `client/lib/services/websocket_service.dart` | 1a |
| 28 | `client/packages/` | — |

## Build Order

```
Phase 0a (Settings Service)
Phase 0b (Settings Router)
Phase 0d (Tailscale Service)
Phase 0c (Welcome Endpoint)
Phase 0e (WS Greeting Inject)
    │
    ▼
Phase 1a (Server Config)
Phase 1b (Settings Service client)
    │
    ├──► Phase 2 (Onboarding) ──► Phase 3 (Settings Screen)
    │
    └──► Phase 4 (Desktop Overlay) ──► Phase 5 (Wearable Bridge) ──► Phase 6 (Persistence)
```
