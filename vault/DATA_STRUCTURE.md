# Jarvis App Data Structure

## 1. User Profile

```javascript
const UserProfile = {
  id: "string",
  name: "string",
  avatar: "string (URL)",
  createdAt: "Date",
  settings: {
    theme: "dark" | "light",
    language: "en" | "fil",
    voiceEnabled: true,
    wakeWord: "Hey Jarvis",
    autoConnect: true
  }
};
```

---

## 2. Device Registry

```javascript
const DeviceRegistry = {
  userId: "string",
  devices: [
    {
      id: "string",
      name: "string",
      type: "phone" | "pc" | "laptop" | "cctv" | "smart-home",
      platform: "android" | "ios" | "windows" | "linux",
      status: "online" | "offline" | "sleeping",
      ip: "string",
      tailscaleIp: "string",
      capabilities: [
        "screen-share",
        "voice",
        "camera",
        "adb",
        "ssh",
        "rdp",
        "rtsp"
      ],
      lastSeen: "Date",
      battery: "number (0-100)",
      signal: "strong" | "medium" | "weak"
    }
  ]
};
```

---

## 3. Conversation History

```javascript
const Conversation = {
  id: "string",
  userId: "string",
  startedAt: "Date",
  messages: [
    {
      id: "string",
      role: "user" | "jarvis",
      content: "string",
      type: "text" | "voice" | "screen",
      timestamp: "Date",
      metadata: {
        sttConfidence: "number",
        llmModel: "string",
        responseTime: "number (ms)",
        tokens: "number"
      }
    }
  ]
};
```

---

## 4. Avatar State

```javascript
const AvatarState = {
  currentState: "idle" | "listening" | "thinking" | "speaking" | "error",
  color: "#00d4ff",
  animations: {
    breathing: {
      outerRing: { speed: 4, amplitude: 0.03 },
      middleRing: { speed: 3, amplitude: 0.05 },
      innerRing: { speed: 2.5, amplitude: 0.06 },
      core: { speed: 3, amplitude: 0.08 },
      reactor: { speed: 2, amplitude: 0.05 },
      glow: { speed: 5, amplitude: 0.2 }
    },
    transitions: {
      popIn: { duration: 400, easing: "cubic-bezier(0.68, -0.55, 0.265, 1.55)" },
      ripple: { duration: 600, count: 3 },
      ringPop: { duration: 500, sizes: [120, 160, 200, 240, 280] }
    }
  },
  wordPulse: {
    active: false,
    currentWord: "",
    pulseIntensity: 1
  }
};
```

---

## 5. Voice Session

```javascript
const VoiceSession = {
  id: "string",
  userId: "string",
  status: "idle" | "listening" | "processing" | "speaking",
  startedAt: "Date",
  
  stt: {
    engine: "whisper" | "vosk",
    language: "en",
    confidence: "number",
    transcript: "string"
  },
  
  tts: {
    engine: "piper" | "edge-tts",
    voice: "en_US-lessac-medium",
    speed: 1.0,
    pitch: 1.0,
    isSpeaking: false,
    currentWord: "string",
    wordIndex: "number"
  },
  
  llm: {
    model: "llama3.2" | "llava:7b",
    temperature: 0.7,
    maxTokens: 2048,
    systemPrompt: "string",
    response: "string",
    tokens: {
      prompt: "number",
      completion: "number",
      total: "number"
    }
  }
};
```

---

## 6. Screen Share Session

```javascript
const ScreenShareSession = {
  id: "string",
  deviceId: "string",
  source: "phone" | "pc",
  status: "inactive" | "starting" | "active" | "paused",
  startedAt: "Date",
  
  capture: {
    fps: 1,
    quality: 80,
    resolution: { width: 1920, height: 1080 },
    format: "jpeg"
  },
  
  analysis: {
    enabled: true,
    interval: 5000,
    lastAnalysis: "Date",
    description: "string",
    objects: ["string"],
    text: "string"
  },
  
  wsConnection: "WebSocket"
};
```

---

## 7. Command Registry

```javascript
const CommandRegistry = {
  commands: [
    {
      id: "string",
      name: "string",
      alias: ["string"],
      category: "system" | "device" | "media" | "smart-home",
      handler: "function",
      requiresAuth: false,
      enabled: true
    }
  ]
};

// Example commands:
const commands = [
  { name: "what-time", alias: ["time", "what time"], handler: "getTime" },
  { name: "open-app", alias: ["open", "launch"], handler: "openApp" },
  { name: "screen-share", alias: ["share screen", "show screen"], handler: "startScreenShare" },
  { name: "volume", alias: ["set volume", "volume"], handler: "setVolume" },
  { name: "play-music", alias: ["play", "music"], handler: "playMusic" },
  { name: "camera", alias: ["show camera", "cctv"], handler: "showCamera" },
  { name: "lights", alias: ["turn on lights", "lights"], handler: "controlLights" }
];
```

---

## 8. App State (Redux/Zustand)

```javascript
const AppState = {
  // User
  user: UserProfile,
  
  // Devices
  devices: DeviceRegistry,
  activeDevice: Device | null,
  
  // Conversations
  conversations: Conversation[],
  currentConversation: Conversation | null,
  
  // Avatar
  avatar: AvatarState,
  
  // Voice
  voice: VoiceSession,
  
  // Screen
  screen: ScreenShareSession,
  
  // UI
  ui: {
    sidebarOpen: false,
    settingsOpen: false,
    currentScreen: "home" | "devices" | "settings" | "chat"
  },
  
  // Connection
  connection: {
    status: "connected" | "disconnected" | "connecting",
    wsUrl: "ws://100.x.x.x:8000/ws",
    reconnectAttempts: 0,
    lastPing: "Date"
  }
};
```

---

## 9. Database Schema (SQLite/Realm)

```sql
-- Users Table
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT,
  avatar TEXT,
  created_at DATETIME,
  settings JSON
);

-- Devices Table
CREATE TABLE devices (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  name TEXT,
  type TEXT,
  platform TEXT,
  ip TEXT,
  tailscale_ip TEXT,
  capabilities JSON,
  status TEXT,
  last_seen DATETIME,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Conversations Table
CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  started_at DATETIME,
  ended_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Messages Table
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT,
  role TEXT,
  content TEXT,
  type TEXT,
  timestamp DATETIME,
  metadata JSON,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Commands Table
CREATE TABLE commands (
  id TEXT PRIMARY KEY,
  name TEXT,
  alias JSON,
  category TEXT,
  handler TEXT,
  enabled BOOLEAN
);
```

---

## 10. API Endpoints

```javascript
const API = {
  // WebSocket
  ws: {
    connect: "ws://100.x.x.x:8000/ws",
    events: {
      send: "user-message",
      receive: "jarvis-response",
      voice: "voice-data",
      screen: "screen-data",
      state: "avatar-state"
    }
  },
  
  // REST (for settings/config)
  rest: {
    GET_DEVICES: "/api/devices",
    GET_CONVERSATIONS: "/api/conversations",
    GET_SETTINGS: "/api/settings",
    UPDATE_SETTINGS: "/api/settings",
    SEND_COMMAND: "/api/command"
  }
};
```

---

## Data Flow

```
+-----------------------------------------------------+
|                      PHONE APP                       |
|                                                      |
|  User Input --> Command Parser --> WebSocket --> Backend |
|                                                      |
|  Avatar State <-- WebSocket <-- Backend Response     |
|                                                      |
+-----------------------------------------------------+
                         |
                         v
+-----------------------------------------------------+
|                    HP ELITEDESK                       |
|                                                      |
|  WebSocket --> FastAPI --> Ollama (LLM)              |
|                    |                                  |
|                    +--> Whisper (STT)                 |
|                    +--> Piper (TTS)                   |
|                    +--> ADB (Phone)                   |
|                    +--> SSH (PC)                      |
|                    +--> RTSP (CCTV)                   |
|                    +--> MQTT (Smart Home)             |
|                    +--> Wearable (Health)             |
|                                                      |
+-----------------------------------------------------+
```

---

## 11. Smart Home Device

```javascript
const SmartDevice = {
  id: "string",
  name: "string",
  type: "light" | "switch" | "thermostat" | "lock" | "fan" | "curtain" | "sensor" | "plug" | "speaker" | "camera",
  protocol: "mqtt" | "http" | "hue" | "tasmota" | "shelly",
  ip: "string",
  topic: "string (MQTT topic)",
  room: "string",
  is_online: "boolean",
  is_on: "boolean",
  brightness: "number (0-100)",
  color: "string (#hex)",
  temperature: "number",
  humidity: "number",
  battery: "number (0-100)",
  state: "object",
  capabilities: ["string"],
  last_update: "number (timestamp)"
};
```

---

## 12. Wearable Device

```javascript
const WearableDevice = {
  id: "string",
  name: "string",
  type: "smartwatch" | "fitness_band" | "smart_ring" | "medical_device",
  platform: "android" | "ios" | "wearos",
  is_online: "boolean",
  battery: "number (0-100)",
  firmware_version: "string",
  last_sync: "number (timestamp)",
  health_summary: {
    heart_rate: {
      current: "number (bpm)",
      unit: "bpm",
      avg: "number",
      min: "number",
      max: "number"
    },
    spo2: {
      current: "number (0-100)",
      unit: "%",
      avg: "number"
    },
    steps: {
      current: "number",
      today_total: "number",
      unit: "steps"
    },
    sleep: {
      current: "number (hours)",
      unit: "hrs"
    },
    calories: {
      today_total: "number",
      unit: "kcal"
    },
    stress: {
      current: "number (0-100)",
      unit: "level"
    },
    body_temperature: {
      current: "number",
      unit: "°F" | "°C"
    }
  }
};
```

---

## 13. Camera (RTSP)

```javascript
const CameraDevice = {
  id: "string",
  name: "string",
  url: "string (RTSP URL)",
  username: "string",
  password: "string",
  type: "cctv" | "doorbell" | "indoor" | "outdoor",
  location: "string",
  is_online: "boolean",
  is_streaming: "boolean",
  viewer_count: "number",
  fps: "number",
  quality: "number (JPEG quality)"
};
```

---

## 14. Command Registry

```javascript
const CommandPattern = {
  patterns: ["string (regex)"],
  handler: "string",
  description: "string",
  category: "system" | "smart_home" | "camera" | "health" | "screen" | "media" | "info",
  examples: ["string"]
};

// Example command categories:
const CommandCategories = {
  system: ["what time", "what date", "remind me"],
  smart_home: ["turn on", "turn off", "set brightness", "lock door"],
  camera: ["show cameras", "show camera", "take photo"],
  health: ["heart rate", "blood oxygen", "steps", "sleep"],
  screen: ["share screen", "stop screen"],
  media: ["play music", "stop music"],
  info: ["weather", "search"]
};
```

---

## 15. Notification

```javascript
const Notification = {
  id: "string",
  title: "string",
  message: "string",
  type: "info" | "health" | "device" | "security" | "success" | "error",
  timestamp: "Date",
  is_read: "boolean"
};
```

---

## Related

- [[AGENTS]] — project rules and architecture
- [[ROADMAP]] — project timeline
- [[SETUP]] — installation guide
- [[API_DOCS]] — backend API reference
- [[JARVIS_ENHANCEMENT_PLAN]] — future features
- [[Memory Map]] — vault index
