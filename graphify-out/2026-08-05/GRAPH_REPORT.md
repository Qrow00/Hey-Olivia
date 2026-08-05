# Graph Report - Hey-Olivia  (2026-08-05)

## Corpus Check
- 282 files · ~166,891 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3695 nodes · 5192 edges · 221 communities (196 shown, 25 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 71 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3084ea95`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- websocket.py
- voice_service.dart
- index.ts
- monitoring_service.dart
- win32_window.cpp
- DevicePlugin
- home_screen.dart
- HermesBrowserService
- smart_home.py
- devices_screen.dart
- SystemCommandService
- camera_screen.dart
- onboarding_screen.dart
- specs_check_screen.dart
- AppDelegate
- main_screen.dart
- settings_screen.dart
- device_card.dart
- MicRecorderPlugin
- monitoring_screen.dart
- camera_service.dart
- browser_screen.dart
- vision_service.dart
- cameras.py
- health_screen.dart
- avatar_widget.dart
- settings_service.dart
- devices.py
- screen_share_screen.dart
- overlay_widget.dart
- browser_service.dart
- screen_share_service.dart
- browser.py
- my_application.cc
- smart_home_screen.dart
- hardware_detector.py
- wearable_screen.dart
- wearable_service.dart
- device_service.dart
- smart_home_service.dart
- compilerOptions
- ScreenCaptureService
- CommandRegistry
- PersonalityService
- VoiceSession
- personality_screen.dart
- server_config.dart
- websocket_service.dart
- RAGService
- compact_avatar_widget.dart
- personality.py
- WearableService
- ProfileMemory
- main.dart
- health_bridge_service.dart
- voice_profiles.py
- ScreenShareService
- J.A.R.V.I.S. Master Plan — Multi-Device Architecture
- ActivityLogger
- MonitoringService
- server.cjs
- settings.py
- DeviceMeshService
- KnowledgeService
- VoiceProfileService
- overlay_manager.dart
- package.json
- screen_share.py
- system.py
- voice.py
- DateTime
- AuthService
- PersonalityEnhancer
- SuggestionEngine
- SystemConfigService
- mic_recorder.dart
- main.py
- AlertEngine
- State
- wWinMain
- test_api.py
- commands.py
- BriefingService
- VisionService
- manifest.json
- OCRService
- ScreenContextService
- TailscaleService
- dart:convert
- Endpoints
- auth.py
- EmailService
- thermal_diag_logger.py
- CodeBurn token usage tracker.md
- NewsService
- CustomPainter
- conversations.py
- WeatherService
- Subagent-Driven Development
- package:flutter/material.dart
- J.A.R.V.I.S. Setup Guide
- graphify.js
- J.A.R.V.I.S. Setup Guide
- DiagnosticsService
- String?
- Pinned Issues.md
- Jarvis App Data Structure
- Jarvis App Data Structure
- vision.py
- Win32Window
- WebSocket Message Types
- Jarvis Enhancement Plan — 8 Phases
- Endpoints
- Test-Driven Development (TDD)
- Jarvis Enhancement Plan — 8 Phases
- Project Memory
- Routines & Automation
- TEMPORARY — Laptop random shutdown diagnosis
- Memory Map
- Morning Briefing
- Personality System
- J.A.R.V.I.S. MVP Roadmap (1-2 Months)
- System Monitoring
- J.A.R.V.I.S. — opencode Instructions
- MessageHandler
- Device Mesh
- MessageHandler
- Camera & Vision System
- Smart Home Integration
- Voice Pipeline
- Jarvis AI Assistant — Project Rules
- Browser Automation
- Frontend Design
- Memory Map
- CodeBurn — Token/Cost Tracker
- Graphify — Knowledge Graph for Hey-Olivia
- Headroom — Context Compression for opencode
- Health & Wearables
- GTX 1050 cannot JIT Ollama CUDA PTX.md
- Ponytail — Minimalism Decision Ladder
- RegisterPlugins
- opencode.json
- Project scope.md
- Edge-TTS over Piper for TTS.md
- Local-first architecture no cloud APIs.md
- Voice Mode Rebuild Around openWakeWord — Design
- jarvis_app
- LaunchImage.imageset/README.md
- theme.dart
- Visual Companion Guide
- Code Review Reception
- Voice Mode Rebuild Around openWakeWord — Implementation Plan
- Finishing a Development Branch
- Root Cause Tracing
- Systematic Debugging
- Using Git Worktrees
- Persuasion Principles for Skill Design
- Dispatching Parallel Agents
- Writing Skills
- Testing Skills With Subagents
- Executing Plans
- Defense-in-Depth Validation
- Writing Plans
- [Analysis Title]
- Returns: "OK" or lists conflicts
- Condition-Based Waiting
- Verification Before Completion
- Skill structure
- Iron Man JARVIS UI — Avatar Redesign + App Theme
- helper.js
- OpenCode Tool Mapping
- Skill authoring best practices
- render-graphs.js
- Global Constraints
- Brainstorming Ideas Into Designs
- ThermalLoggerService
- using-superpowers/SKILL.md
- REFACTOR Phase: Close Loopholes (Stay Green)
- Skill Discovery Optimization (SDO)
- Bulletproofing Skills Against Rationalization
- anthropic-best-practices.md
- Anti-Patterns
- Testing All Skill Types
- RED-GREEN-REFACTOR for Skills
- VERIFY GREEN: Pressure Testing
- broadcast
- Checklist for effective Skills
- Core principles
- File Organization
- Skill Types
- Example: TDD Skill Bulletproofing
- spec-document-reviewer-prompt.md
- plan-document-reviewer-prompt.md
- _SpecsCheckScreenState
- system_service.dart
- handle_voice_mode_start
- Evaluation and iteration

## God Nodes (most connected - your core abstractions)
1. `websocket_endpoint()` - 84 edges
2. `safe_send()` - 75 edges
3. `SystemCommandService` - 45 edges
4. `VoiceSession` - 44 edges
5. `SendCollector` - 34 edges
6. `HermesBrowserService` - 30 edges
7. `DiagnosticsService` - 24 edges
8. `CommandRegistry` - 22 edges
9. `Win32Window` - 22 edges
10. `Writing Skills` - 22 edges

## Surprising Connections (you probably didn't know these)
- `add_device()` --calls--> `Device`  [EXTRACTED]
  backend/app/routers/devices.py → types/device.ts
- `ClientInfo` --uses--> `VoiceSession`  [INFERRED]
  backend/app/routers/websocket.py → backend/app/services/voice_session_service.py
- `ClientInfo` --uses--> `WearableDevice`  [INFERRED]
  backend/app/routers/websocket.py → backend/app/services/wearable_service.py
- `OnCreate` --calls--> `RegisterPlugins()`  [INFERRED]
  client/windows/runner/flutter_window.h → client/windows/flutter/generated_plugin_registrant.cc
- `wWinMain()` --calls--> `CreateAndAttachConsole()`  [INFERRED]
  client/windows/runner/main.cpp → client/windows/runner/utils.cpp

## Import Cycles
- None detected.

## Communities (221 total, 25 thin omitted)

### Community 0 - "websocket.py"
Cohesion: 0.10
Nodes (74): handle_activity_log(), handle_activity_processes(), handle_activity_window(), handle_audio_frame(), handle_briefing_config(), handle_browser_click(), handle_browser_close_tab(), handle_browser_create_session() (+66 more)

### Community 1 - "voice_service.dart"
Cohesion: 0.03
Nodes (62): _alwaysListening, _audioStreamSub, avatarState, _avatarStateController, _currentPlayer, _currentState, _detectDefaultMic, dispose (+54 more)

### Community 2 - "index.ts"
Cohesion: 0.06
Nodes (60): API, APIConfig, RESTEndpoints, WSConfig, WSEventType, AppState, ConnectionState, ConnectionStatus (+52 more)

### Community 3 - "monitoring_service.dart"
Cohesion: 0.03
Nodes (65): _activityController, ActivityEntry, _activityLog, alert, _alertController, AlertData, alertDetails, _alerts (+57 more)

### Community 4 - "win32_window.cpp"
Cohesion: 0.15
Nodes (16): wchar_t, Scale(), Create, Destroy, SetQuitOnClose, Show, UpdateTheme, Win32Window::Win32Window() (+8 more)

### Community 5 - "DevicePlugin"
Cohesion: 0.06
Nodes (19): ABC, DevicePlugin, PluginInfo, PluginManager, MotionDetectorPlugin, disable_plugin(), enable_plugin(), execute_plugin_command() (+11 more)

### Community 6 - "home_screen.dart"
Cohesion: 0.03
Nodes (57): _addChatMessage, _avatarState, _avatarSubscription, _bg, build, _buildAvatarSection, _buildBottomPanel, _buildChatHistory (+49 more)

### Community 7 - "HermesBrowserService"
Cohesion: 0.08
Nodes (13): BrowserSession, _BrowserWorker, HermesBrowserService, Any, Navigate to YouTube search, then click the first video to play it., Get a summary of clickable elements and key content on the page., Get info about all tabs in a session., Get info about all tabs across all sessions or a specific session. (+5 more)

### Community 8 - "smart_home.py"
Cohesion: 0.10
Nodes (28): add_device(), connect_mqtt(), control_device(), delete_device(), DeviceControl, execute_scene(), get_device(), get_devices() (+20 more)

### Community 9 - "devices_screen.dart"
Cohesion: 0.07
Nodes (30): _bg, build, _buildDetailRow, _buildDeviceDetailsSheet, _buildDeviceList, _buildFilterBar, _buildFilterChip, _buildSummaryBar (+22 more)

### Community 11 - "camera_screen.dart"
Cohesion: 0.04
Nodes (47): _alertSubscription, _analyzeCurrentCamera, _askQuestion, _bg, build, _buildActionButton, _buildCameraCard, _buildCameraList (+39 more)

### Community 12 - "onboarding_screen.dart"
Cohesion: 0.05
Nodes (43): _authToken, build, _buildCompleteStep, _buildConnectionResult, _buildConnectStep, _buildHudButton, _buildProfileStep, _buildServerInfo (+35 more)

### Community 13 - "specs_check_screen.dart"
Cohesion: 0.05
Nodes (41): Animation, _backendOnline, build, _buildErrorState, _buildHeader, _buildHudReadout, _buildLaunchBar, _buildModelLine (+33 more)

### Community 14 - "AppDelegate"
Cohesion: 0.06
Nodes (28): AppDelegate, Any, Bool, SceneDelegate, RunnerTests, RegisterGeneratedPlugins(), AppDelegate, Bool (+20 more)

### Community 15 - "main_screen.dart"
Cohesion: 0.04
Nodes (47): camera_screen.dart, _bg, build, _buildBody, _buildDrawer, _buildDrawerHeader, _buildNav, _cameraService (+39 more)

### Community 16 - "settings_screen.dart"
Cohesion: 0.05
Nodes (42): _bg, _buildDeviceTile, _buildSection, _buildSwitchTile, _buildTapTile, _configMissing, createState, _darkMode (+34 more)

### Community 17 - "device_card.dart"
Cohesion: 0.11
Nodes (18): _FullscreenViewer, build, _buildActions, _buildCapabilities, _buildHeader, _buildStatItem, _buildStats, _buildStatusBadge (+10 more)

### Community 18 - "MicRecorderPlugin"
Cohesion: 0.08
Nodes (19): AudioRecord, HealthBridgePlugin, MethodCall, MethodChannel, IntArray, Intent, MethodChannel, MainActivity (+11 more)

### Community 19 - "monitoring_screen.dart"
Cohesion: 0.05
Nodes (39): _activity, _activitySub, _alerts, _alertSub, _bg, build, _buildActivityTab, _buildAlertsTab (+31 more)

### Community 20 - "camera_service.dart"
Cohesion: 0.06
Nodes (35): addCamera, allCameras, baseUrl, CameraDevice, CameraFrame, cameraId, _cameras, CameraService (+27 more)

### Community 21 - "browser_screen.dart"
Cohesion: 0.06
Nodes (35): _bg, BrowserScreen, _BrowserScreenState, browserService, build, _buildBrowserView, _buildSessionPlaceholder, _cancelSubscriptions (+27 more)

### Community 22 - "vision_service.dart"
Cohesion: 0.06
Nodes (34): _activeObservationSession, activeSession, _alertController, alerts, analyzeCamera, askAboutCamera, baseUrl, camera (+26 more)

### Community 23 - "cameras.py"
Cohesion: 0.10
Nodes (19): add_camera(), CameraCreate, CameraUpdate, delete_camera(), get_camera(), get_cameras(), get_online_cameras(), BaseModel (+11 more)

### Community 24 - "health_screen.dart"
Cohesion: 0.06
Nodes (30): _bg, build, _buildAlertsSection, _buildBattery, _buildChip, _buildDashboard, _buildDeviceHeader, _buildNoDevice (+22 more)

### Community 25 - "avatar_widget.dart"
Cohesion: 0.07
Nodes (29): build, _center, _controller, createState, currentState, _cx, _cy, didUpdateWidget (+21 more)

### Community 26 - "settings_service.dart"
Cohesion: 0.06
Nodes (31): all, _authHeaders, _config, darkMode, fetch, _health, healthAlertsEnabled, heartRateAlerts (+23 more)

### Community 27 - "devices.py"
Cohesion: 0.14
Nodes (20): add_device(), detect_capabilities(), detect_device_capabilities(), device_heartbeat(), device_status_summary(), _device_to_dict(), DeviceCreate, DeviceUpdate (+12 more)

### Community 28 - "screen_share_screen.dart"
Cohesion: 0.06
Nodes (32): _analysisResult, _analysisSubscription, _bg, build, _buildAnalysisPanel, _buildControlBar, _buildControlButton, _buildViewer (+24 more)

### Community 29 - "overlay_widget.dart"
Cohesion: 0.06
Nodes (34): _avatarState, _bg, build, _buildControls, _buildHealthBar, _buildMenuButton, _buildTitleBar, _connect (+26 more)

### Community 30 - "browser_service.dart"
Cohesion: 0.06
Nodes (30): BrowserService, click, createSession, _currentSessionId, _currentTitle, _currentUrl, destroySession, dispose (+22 more)

### Community 31 - "screen_share_service.dart"
Cohesion: 0.07
Nodes (28): analysis, _analysisController, _captureAndSendFrame, _channel, _currentSessionId, dispose, _fps, _frameController (+20 more)

### Community 32 - "browser.py"
Cohesion: 0.15
Nodes (26): click(), ClickRequest, create_session(), CreateSessionRequest, destroy_session(), extract_content(), ExtractRequest, get_session() (+18 more)

### Community 33 - "my_application.cc"
Cohesion: 0.09
Nodes (22): fl_register_plugins(), main(), first_frame_cb(), my_application_activate(), my_application_class_init(), my_application_dispose(), my_application_init(), my_application_local_command_line() (+14 more)

### Community 34 - "smart_home_screen.dart"
Cohesion: 0.08
Nodes (23): build, _buildColorPicker, _buildControlSheet, _buildDeviceCard, _buildDeviceGrid, _buildNoDevices, _buildRoomFilter, createState (+15 more)

### Community 35 - "hardware_detector.py"
Cohesion: 0.18
Nodes (12): detect_gpu(), get_hardware_profile(), GpuInfo, ollama_llm_library(), ollama_use_cpu(), ollama_version(), _parse_cc(), _parse_version() (+4 more)

### Community 36 - "wearable_screen.dart"
Cohesion: 0.09
Nodes (23): build, _buildAlertsSection, _buildBatteryIndicator, _buildDeviceHeader, _buildHealthDashboard, _buildNoDevice, _buildStatusChip, _buildVitalRow (+15 more)

### Community 37 - "wearable_service.dart"
Cohesion: 0.08
Nodes (23): _alertController, alerts, allDevices, baseUrl, _deviceController, devices, dispose, fetchDevices (+15 more)

### Community 38 - "device_service.dart"
Cohesion: 0.09
Nodes (22): addDevice, _baseUrl, currentDevices, _deviceEventController, deviceEvents, devices, _devicesController, DeviceService (+14 more)

### Community 39 - "smart_home_service.dart"
Cohesion: 0.09
Nodes (22): addDevice, allDevices, baseUrl, connectMQTT, _control, _deviceController, _devices, deviceUpdates (+14 more)

### Community 40 - "compilerOptions"
Cohesion: 0.09
Nodes (22): dist, node_modules, types/**/*.ts, compilerOptions, baseUrl, declaration, declarationMap, esModuleInterop (+14 more)

### Community 41 - "ScreenCaptureService"
Cohesion: 0.13
Nodes (10): android, Intent, ScreenCaptureService, IBinder, Image, ImageReader, MediaProjection, Notification (+2 more)

### Community 42 - "CommandRegistry"
Cohesion: 0.14
Nodes (11): CommandPattern, CommandRegistry, test_command_list_not_empty(), test_get_all_commands(), test_get_categories(), test_parse_empty(), test_parse_lights_on(), test_parse_run_diagnostics() (+3 more)

### Community 43 - "PersonalityService"
Cohesion: 0.21
Nodes (5): Opinion, PersonalityService, ProfileData, Path, StyleProfile

### Community 44 - "VoiceSession"
Cohesion: 0.07
Nodes (46): _load_vad(), _load_wake_model(), Enum, Server-side voice session: openWakeWord wake detection + Silero VAD command…, SessionPhase, strip_wake_phrase(), VoiceSession, FakeProfile (+38 more)

### Community 45 - "personality_screen.dart"
Cohesion: 0.09
Nodes (23): _bg, build, _buildFeedback, _buildHeader, _buildStats, _buildStyleSection, createState, _error (+15 more)

### Community 46 - "server_config.dart"
Cohesion: 0.10
Nodes (19): baseUrl, discoverViaTailscan, fromJson, _getConfigPath, _instance, load, profileId, profileName (+11 more)

### Community 47 - "websocket_service.dart"
Cohesion: 0.10
Nodes (19): _channel, connect, dispose, exitApp, _exitController, _isConnected, _messageController, messages (+11 more)

### Community 48 - "RAGService"
Cohesion: 0.22
Nodes (3): DocumentChunk, RAGService, ndarray

### Community 49 - "compact_avatar_widget.dart"
Cohesion: 0.11
Nodes (19): AnimationController, build, _color, CompactAvatarWidget, _CompactAvatarWidgetState, _controller, createState, currentState (+11 more)

### Community 50 - "personality.py"
Cohesion: 0.22
Nodes (17): adjust_feedback(), FeedbackAdjust, get_opinions(), get_personality(), get_reflections(), get_system_prompt(), learn_opinion(), learn_preference() (+9 more)

### Community 51 - "WearableService"
Cohesion: 0.07
Nodes (20): get_alerts(), get_health_history(), get_health_summary(), get_wearable(), get_wearables(), HealthUpdate, BaseModel, delete (+12 more)

### Community 52 - "ProfileMemory"
Cohesion: 0.17
Nodes (3): ConversationMemoryManager, _file_for(), ProfileMemory

### Community 53 - "main.dart"
Cohesion: 0.13
Nodes (14): _bg, build, _checkConfig, createState, _hasConfig, _hud, initState, _loading (+6 more)

### Community 54 - "health_bridge_service.dart"
Cohesion: 0.12
Nodes (16): _channel, _deviceId, dispose, HealthBridgeService, isAvailable, _observing, _pollAndRelay, _pollTimer (+8 more)

### Community 55 - "voice_profiles.py"
Cohesion: 0.19
Nodes (15): ActivateProfile, create_profile(), delete_profile(), get_active_profile(), get_tts_config(), list_profiles(), ProfileCreate, ProfileUpdate (+7 more)

### Community 56 - "ScreenShareService"
Cohesion: 0.17
Nodes (4): CaptureConfig, ScreenAnalysis, ScreenShareService, ScreenShareSession

### Community 57 - "J.A.R.V.I.S. Master Plan — Multi-Device Architecture"
Cohesion: 0.06
Nodes (32): 0a — Settings Service (`backend/app/services/settings_service.py`) **NEW**, 0b — Update Settings Router (`backend/app/routers/settings.py`) **MODIFY**, 0c — Welcome Endpoint (`backend/app/routers/system.py`) **MODIFY**, 0d — Tailscale Service (`backend/app/services/tailscale_service.py`) **NEW**, 0e — Inject Settings + Tailscale into WebSocket Greeting **MODIFY**, 1a — server_config.dart (`client/lib/services/server_config.dart`) **NEW**, 1b — settings_service.dart (`client/lib/services/settings_service.dart`) **NEW**, 2a — onboarding_screen.dart (`client/lib/screens/onboarding_screen.dart`) **NEW** (+24 more)

### Community 59 - "MonitoringService"
Cohesion: 0.08
Nodes (9): MonitoringService, FakeProc, anyio, fixture, svc(), test_broadcast_voice_alert_sends_base64_audio(), test_broadcast_voice_alert_silent_on_tts_error(), test_collect_once_includes_process_metrics() (+1 more)

### Community 60 - "server.cjs"
Cohesion: 0.06
Nodes (55): RFC-6455, bootstrapPage(), brandMarkup(), broadcast(), browserLauncherForPlatform(), chmodOwnerOnly(), clients, companionUrl() (+47 more)

### Community 61 - "settings.py"
Cohesion: 0.19
Nodes (12): require_auth(), get_settings(), get_settings_public(), patch_settings(), BaseModel, get, post, put (+4 more)

### Community 65 - "overlay_manager.dart"
Cohesion: 0.14
Nodes (13): bool get, _enterOverlay, _exitOverlay, init, _instance, _isOverlay, _overlay, OverlayManager (+5 more)

### Community 66 - "package.json"
Cohesion: 0.14
Nodes (13): description, devDependencies, typescript, engines, node, name, scripts, build (+5 more)

### Community 67 - "screen_share.py"
Cohesion: 0.28
Nodes (12): analyze_screen(), AnalyzeRequest, delete_session(), get_session(), list_sessions(), BaseModel, delete, get (+4 more)

### Community 68 - "system.py"
Cohesion: 0.24
Nodes (12): apply_tier(), ConfigUpdate, get_config(), get_models(), get_specs(), get_tailscale(), health(), BaseModel (+4 more)

### Community 69 - "voice.py"
Cohesion: 0.26
Nodes (12): chat_completion(), ChatRequest, list_voices(), BaseModel, get, post, speech_to_text(), text_to_speech() (+4 more)

### Community 75 - "mic_recorder.dart"
Cohesion: 0.15
Nodes (12): _events, isSupported, _method, MicRecorder, _pcm, start, stop, package:flutter/services.dart (+4 more)

### Community 76 - "main.py"
Cohesion: 0.23
Nodes (9): api_root(), get, root(), service_enabled(), shutdown(), startup(), client(), fixture (+1 more)

### Community 78 - "State"
Cohesion: 0.16
Nodes (18): JarvisApp, _JarvisAppState, OverlayWidget, _OverlayWidgetState, HealthScreen, _HealthScreenState, HomeScreen, _HomeScreenState (+10 more)

### Community 79 - "wWinMain"
Cohesion: 0.24
Nodes (9): wWinMain(), string, wchar_t, CreateAndAttachConsole(), GetCommandLineArguments(), Utf8FromUtf16(), _In_, _In_opt_ (+1 more)

### Community 80 - "test_api.py"
Cohesion: 0.33
Nodes (10): anyio, test_api_root(), test_get_commands(), test_get_creameras(), test_get_devices(), test_get_plugin_capabilities(), test_get_plugins(), test_get_smart_home() (+2 more)

### Community 81 - "commands.py"
Cohesion: 0.29
Nodes (10): CommandExecute, CommandParse, execute_command(), get_categories(), get_commands(), get_commands_by_category(), parse_command(), BaseModel (+2 more)

### Community 83 - "VisionService"
Cohesion: 0.17
Nodes (3): ObservationSession, SceneObservation, VisionService

### Community 84 - "manifest.json"
Cohesion: 0.18
Nodes (10): background_color, description, display, icons, name, orientation, prefer_related_applications, short_name (+2 more)

### Community 88 - "dart:convert"
Cohesion: 0.12
Nodes (15): baseUrl, getStatus, learnOpinion, PersonalityService, setFeedback, setName, updateStyle, baseUrl (+7 more)

### Community 89 - "Endpoints"
Cohesion: 0.07
Nodes (27): API Reference, Base URL, Browser (Hermes), Cameras (RTSP), Client → Server, Commands, Conversations, Devices (+19 more)

### Community 90 - "auth.py"
Cohesion: 0.32
Nodes (7): list_profiles(), login(), LoginRequest, logout(), BaseModel, get, post

### Community 92 - "thermal_diag_logger.py"
Cohesion: 0.50
Nodes (7): iso_now(), main(), Path, read_cpu_temp(), read_gpu(), _run(), start_shutdown_watchdog()

### Community 93 - "CodeBurn token usage tracker.md"
Cohesion: 0.08
Nodes (21): Application, Implemented (2026-08-05), Key commands, Problem, Quick start, Solution, Supported providers (that apply here), Waste detection (+13 more)

### Community 95 - "CustomPainter"
Cohesion: 0.29
Nodes (7): _AvatarPainter, _GridPainter, _GridPainter, _ScanRingPainter, JarvisHudPainter, _CompactAvatarPainter, CustomPainter

### Community 96 - "conversations.py"
Cohesion: 0.60
Nodes (4): get_conversation(), get_conversations(), AsyncSession, get

### Community 98 - "Subagent-Driven Development"
Cohesion: 0.06
Nodes (28): Code Reviewer Prompt Template, Example Output, Common Rationalizations, Example, How to Request, Platform Adaptation (opencode), Red Flags, Requesting Code Review (+20 more)

### Community 99 - "package:flutter/material.dart"
Cohesion: 0.10
Nodes (17): cardGap, cardPadding, Display, drawerWidth, gridColumns, isLandscape, isPhone, isTablet (+9 more)

### Community 100 - "J.A.R.V.I.S. Setup Guide"
Cohesion: 0.08
Nodes (23): 1. Install Flutter, 1. Install Python Dependencies, 2. Configure Server URL, 2. Install Ollama, 3. Run Client, 3. Start Backend, 4. Configure Tailscale (Optional), Backend (HP EliteDesk) (+15 more)

### Community 102 - "J.A.R.V.I.S. Setup Guide"
Cohesion: 0.08
Nodes (24): 1. Install Flutter, 1. Install Python Dependencies, 2. Configure Server URL, 2. Install Ollama, 3. Run Client, 3. Start Backend, 4. Configure Tailscale (Optional), Backend (HP EliteDesk) (+16 more)

### Community 103 - "DiagnosticsService"
Cohesion: 0.12
Nodes (8): DiagnosticsService, System diagnostics: probe each subsystem and report which are functional., anyio, fixture, svc(), test_run_isolates_failures(), test_run_returns_full_report(), test_run_times_out_slow_check()

### Community 118 - "Pinned Issues.md"
Cohesion: 0.11
Nodes (18): 1. Settings PATCH 307 Redirect — FIXED, 2. Voice service doesn't read selected model — FIXED, 3. LLM parse error on Android client — NOT REPRODUCIBLE BACKEND-SIDE (verified Aug 3), `asyncio.create_subprocess_exec` not supported on Windows — FIXED, Auth, Available Ollama Models, Backend Crashes, Conversation Memory — DONE (+10 more)

### Community 119 - "Jarvis App Data Structure"
Cohesion: 0.11
Nodes (17): 10. API Endpoints, 11. Smart Home Device, 12. Wearable Device, 13. Camera (RTSP), 14. Command Registry, 15. Notification, 1. User Profile, 2. Device Registry (+9 more)

### Community 120 - "Jarvis App Data Structure"
Cohesion: 0.11
Nodes (18): 10. API Endpoints, 11. Smart Home Device, 12. Wearable Device, 13. Camera (RTSP), 14. Command Registry, 15. Notification, 1. User Profile, 2. Device Registry (+10 more)

### Community 121 - "vision.py"
Cohesion: 0.17
Nodes (21): analyze_camera(), describe_for_command(), get_observation_history(), get_observation_session(), get_observation_sessions(), get_vision_cameras(), ObservationStart, BaseModel (+13 more)

### Community 122 - "Win32Window"
Cohesion: 0.17
Nodes (17): FlutterWindow, flutter_controller_, OnCreate, OnDestroy, project_, DartProject, HWND, Win32Window (+9 more)

### Community 124 - "WebSocket Message Types"
Cohesion: 0.13
Nodes (14): Accessibility Snapshot, Capabilities, Click Element, Create Session, Google Search, JARVIS Browser Skill, Navigate, Response Types (+6 more)

### Community 125 - "Jarvis Enhancement Plan — 8 Phases"
Cohesion: 0.14
Nodes (13): Build Order, Jarvis Enhancement Plan — 8 Phases, New Dependencies, New Flutter Screens/Widgets, Overview, Phase 1: Proactive Monitoring & System Awareness, Phase 2: Morning Briefing, Phase 3: Wake Word Detection (+5 more)

### Community 126 - "Endpoints"
Cohesion: 0.07
Nodes (28): API Reference, Base URL, Browser (Hermes), Cameras (RTSP), Client → Server, Commands, Conversations, Devices (+20 more)

### Community 127 - "Test-Driven Development (TDD)"
Cohesion: 0.08
Nodes (23): Common Rationalizations, Debugging Integration, Example: Bug Fix, Final Rule, Good Tests, Overview, Red Flags - STOP and Start Over, Red-Green-Refactor (+15 more)

### Community 128 - "Jarvis Enhancement Plan — 8 Phases"
Cohesion: 0.14
Nodes (14): Build Order, Jarvis Enhancement Plan — 8 Phases, New Dependencies, New Flutter Screens/Widgets, Overview, Phase 1: Proactive Monitoring & System Awareness, Phase 2: Morning Briefing, Phase 3: Wake Word Detection (+6 more)

### Community 129 - "Project Memory"
Cohesion: 0.17
Nodes (10): Canonical project info, Decisions, learnings, context, Feature documentation, Identity, Memory (vault), Project Memory, Quick start, Run modes (JARVIS_SERVICES env var) (+2 more)

### Community 130 - "Routines & Automation"
Cohesion: 0.15
Nodes (13): Built-in Routines, Components, Custom Routines, Good Night, I'm Leaving, Movie Time, Overview, Related (+5 more)

### Community 131 - "TEMPORARY — Laptop random shutdown diagnosis"
Cohesion: 0.17
Nodes (10): Client machines, GPU (NVIDIA GTX 1050), Server (HP EliteDesk), Active task, Diagnostic tool built Aug 3, Hypotheses (in order of likelihood), Known facts (verified Aug 3), Load test Aug 3 (AI app as workload — DONE) (+2 more)

### Community 132 - "Memory Map"
Cohesion: 0.17
Nodes (12): AI & Personalization, Core Features, Current Issues, Data & Architecture, Future Development, How to Use This Vault, Master Plan, Memory Map (+4 more)

### Community 133 - "Morning Briefing"
Cohesion: 0.17
Nodes (12): Briefing Orchestrator, Calendar Service, Components, Flow, Morning Briefing, News Service, Overview, Related (+4 more)

### Community 134 - "Personality System"
Cohesion: 0.18
Nodes (11): API Endpoints, British Wit Library, Configuration, Contextual Remarks, Features, Overview, Personality Enhancer, Personality System (+3 more)

### Community 135 - "J.A.R.V.I.S. MVP Roadmap (1-2 Months)"
Cohesion: 0.18
Nodes (11): Architecture Overview, J.A.R.V.I.S. MVP Roadmap (1-2 Months), Phase 1: Foundation (Week 1-2) ✅ DONE, Phase 2: Core Voice (Week 3-4) ✅ DONE, Phase 3: Device Management (Week 5-6) ✅ DONE, Phase 4: Screen Sharing (Week 7-8) ✅ DONE, Phase 5: Smart Home & Polish (Week 9-10) ✅ DONE, Phase 6: Future Proofing (Week 11-12) ✅ DONE (+3 more)

### Community 136 - "System Monitoring"
Cohesion: 0.18
Nodes (11): Activity Logger, Alert Engine, Alert Thresholds, Components, Metrics Monitored, Overview, Related, System Monitor (+3 more)

### Community 137 - "J.A.R.V.I.S. — opencode Instructions"
Cohesion: 0.18
Nodes (10): Available Commands, Backend Runtime, graphify, gstack Workflow, J.A.R.V.I.S. — opencode Instructions, Model Rules, Ponytail — Minimalism Decision Ladder, Superpowers Skills (+2 more)

### Community 138 - "MessageHandler"
Cohesion: 0.36
Nodes (10): HWND, LPARAM, LRESULT, UINT, WPARAM, EnableFullDpiSupportIfAvailable(), GetHandle, GetThisFromHandle (+2 more)

### Community 139 - "Device Mesh"
Cohesion: 0.20
Nodes (10): Architecture, Clipboard Sync, Device Mesh, Features, File Transfer, Overview, Push to Phone, Related (+2 more)

### Community 140 - "MessageHandler"
Cohesion: 0.22
Nodes (8): DartProject, HWND, LPARAM, LRESULT, UINT, WPARAM, FlutterWindow::FlutterWindow(), MessageHandler

### Community 141 - "Camera & Vision System"
Cohesion: 0.22
Nodes (9): AI Vision, Camera Types, Camera & Vision System, Endpoints, Models, Observation Mode, Related, RTSP Integration (+1 more)

### Community 142 - "Smart Home Integration"
Cohesion: 0.22
Nodes (9): Broker, Connect, Control Endpoints, Device Types, MQTT Setup, Protocols, Related, Smart Home Integration (+1 more)

### Community 143 - "Voice Pipeline"
Cohesion: 0.20
Nodes (10): Components, LLM (Language Model), Overview, Related, STT (Speech-to-Text), TTS (Text-to-Speech), Voice Flow, Voice Pipeline (+2 more)

### Community 144 - "Jarvis AI Assistant — Project Rules"
Cohesion: 0.25
Nodes (8): Architecture, Backend Structure, Code Conventions, Flutter Structure, Jarvis AI Assistant — Project Rules, Key Files, Local Models, Related

### Community 145 - "Browser Automation"
Cohesion: 0.25
Nodes (8): Browser Automation, Capabilities, Endpoints, Engine, Overview, Related, Voice Commands, WebSocket Events

### Community 146 - "Frontend Design"
Cohesion: 0.29
Nodes (6): Design principles, Frontend Design, Ground it in the subject, More on writing in design, Process: brainstorm, explore, plan, critique, build, critique again, Restraint and self-critique

### Community 147 - "Memory Map"
Cohesion: 0.29
Nodes (6): Context, Decisions, Feature Docs (vault root), Learnings, Memory Map, Reminders (temporary — act on these)

### Community 148 - "CodeBurn — Token/Cost Tracker"
Cohesion: 0.33
Nodes (5): CodeBurn — Token/Cost Tracker, Installed (this machine), Key commands, Usage, Windows notes

### Community 149 - "Graphify — Knowledge Graph for Hey-Olivia"
Cohesion: 0.33
Nodes (5): Graphify — Knowledge Graph for Hey-Olivia, Installed (this machine), Keeping it current, Local-first constraints, Query commands

### Community 150 - "Headroom — Context Compression for opencode"
Cohesion: 0.33
Nodes (5): Headroom — Context Compression for opencode, Installed (this machine), Notes, Proxy operations, Routing opencode through Headroom

### Community 151 - "Health & Wearables"
Cohesion: 0.33
Nodes (6): API Endpoints, Health Metrics, Health & Wearables, Related, Supported Devices, Voice Commands

### Community 152 - "GTX 1050 cannot JIT Ollama CUDA PTX.md"
Cohesion: 0.33
Nodes (5): Current state (Aug 3), Gotchas, Status: SUPERSEDED (2026-08-03), Verified on this machine (Ollama 0.32.4, GTX 1050), Why it appeared broken before

### Community 153 - "Ponytail — Minimalism Decision Ladder"
Cohesion: 0.40
Nodes (4): Examples, How to apply, Ponytail — Minimalism Decision Ladder, Review checklist (when reviewing existing code)

### Community 155 - "opencode.json"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

### Community 156 - "Project scope.md"
Cohesion: 0.50
Nodes (3): Key design principles, What it does NOT do, What J.A.R.V.I.S. does

### Community 157 - "Edge-TTS over Piper for TTS.md"
Cohesion: 0.50
Nodes (3): Consequences, Context, Decision

### Community 158 - "Local-first architecture no cloud APIs.md"
Cohesion: 0.50
Nodes (3): Consequences, Context, Decision

### Community 159 - "Voice Mode Rebuild Around openWakeWord — Design"
Cohesion: 0.08
Nodes (24): Architecture, Backend design, Client design (Flutter), Client → Server, Command endpointing thresholds, Concurrency, Config, Deprecations (+16 more)

### Community 165 - "theme.dart"
Cohesion: 0.12
Nodes (16): accentAmber, accentGreen, accentRed, AppTheme, bg, dataFont, hud, hudDim (+8 more)

### Community 166 - "Visual Companion Guide"
Cohesion: 0.10
Nodes (19): Browser Events Format, Cards (visual designs), Cleaning Up, CSS Classes Available, Design Tips, File Naming, How It Works, Mock elements (wireframe building blocks) (+11 more)

### Community 167 - "Code Review Reception"
Cohesion: 0.12
Nodes (16): Acknowledging Correct Feedback, Code Review Reception, Common Mistakes, Forbidden Responses, From External Reviewers, From your human partner, GitHub Thread Replies, Gracefully Correcting Your Pushback (+8 more)

### Community 168 - "Voice Mode Rebuild Around openWakeWord — Implementation Plan"
Cohesion: 0.12
Nodes (15): File Structure, Global Constraints, Self-Review (run after writing the plan), Task 10: Documentation updates, Task 11: Final verification and manual QA runbook, Task 1: VoiceSession skeleton — phases, buffers, worker, start/stop, Task 2: Wake detection — LISTENING/SPEAKING scan, suppression, barge-in, Task 3: Silero VAD command endpointing (+7 more)

### Community 169 - "Finishing a Development Branch"
Cohesion: 0.12
Nodes (15): Common Rationalizations, Finishing a Development Branch, If your human partner asks to discard the work, Option 1: Merge Locally, Option 2: Push and Create PR, Option 3: Keep As-Is, Overview, Platform Adaptation (opencode) (+7 more)

### Community 170 - "Root Cause Tracing"
Cohesion: 0.12
Nodes (15): 1. Observe the Symptom, 2. Find Immediate Cause, 3. Ask: What Called This?, 4. Keep Tracing Up, 5. Find Original Trigger, Adding Stack Traces, Finding Which Test Causes Pollution, Key Principle (+7 more)

### Community 171 - "Systematic Debugging"
Cohesion: 0.12
Nodes (15): Common Rationalizations, Overview, Phase 1: Root Cause Investigation, Phase 2: Pattern Analysis, Phase 3: Hypothesis and Testing, Phase 4: Implementation, Quick Reference, Red Flags - STOP and Follow Process (+7 more)

### Community 172 - "Using Git Worktrees"
Cohesion: 0.12
Nodes (15): 1a. Native Worktree Tools, 1b. Git Worktree Fallback, Common Rationalizations, Create the Worktree, Directory Selection, Overview, Platform Adaptation (opencode), Quick Reference (+7 more)

### Community 173 - "Persuasion Principles for Skill Design"
Cohesion: 0.12
Nodes (15): 1. Authority, 2. Commitment, 3. Scarcity, 4. Social Proof, 5. Unity, 6. Reciprocity, 7. Liking, Ethical Use (+7 more)

### Community 174 - "Dispatching Parallel Agents"
Cohesion: 0.13
Nodes (14): 1. Identify Independent Domains, 2. Create Focused Agent Tasks, 3. Dispatch in Parallel, 4. Review and Integrate, Agent Prompt Structure, Common Mistakes, Dispatching Parallel Agents, Overview (+6 more)

### Community 175 - "Writing Skills"
Cohesion: 0.13
Nodes (15): Code Examples, Common Rationalizations for Skipping Testing, Directory Structure, Discovery Workflow, Flowchart Usage, Match the Form to the Failure, Overview, Skill Creation Checklist (TDD Adapted) (+7 more)

### Community 176 - "Testing Skills With Subagents"
Cohesion: 0.15
Nodes (13): Common Mistakes (Same as TDD), GREEN Phase: Write Minimal Skill (Make It Pass), Meta-Testing (When GREEN Isn't Working), Overview, Quick Reference (TDD Cycle), Real-World Impact, RED Phase: Baseline Testing (Watch It Fail), TDD Mapping for Skill Testing (+5 more)

### Community 177 - "Executing Plans"
Cohesion: 0.17
Nodes (11): Completion, Context Management, Executing Plans, Execution, For Each Task, Overview, Pausing Between Tasks, Plan Document Location (+3 more)

### Community 178 - "Defense-in-Depth Validation"
Cohesion: 0.17
Nodes (11): Applying the Pattern, Defense-in-Depth Validation, Example from Session, Key Insight, Layer 1: Entry Point Validation, Layer 2: Business Logic Validation, Layer 3: Environment Guards, Layer 4: Debug Instrumentation (+3 more)

### Community 179 - "Writing Plans"
Cohesion: 0.17
Nodes (11): Bite-Sized Task Granularity, Execution Handoff, File Structure, No Placeholders, Overview, Plan Document Header, Scope Check, Self-Review (+3 more)

### Community 180 - "[Analysis Title]"
Cohesion: 0.17
Nodes (12): Advanced: Skills with executable code, [Analysis Title], Anti-patterns to avoid, Avoid offering too many options, Avoid Windows-style paths, Conditional workflow pattern, Examples pattern, Executive summary (+4 more)

### Community 181 - "Returns: "OK" or lists conflicts"
Cohesion: 0.18
Nodes (11): Avoid assuming tools are installed, Create verifiable intermediate outputs, MCP tool references, Next steps, Package dependencies, Returns: "OK" or lists conflicts, Runtime environment, Technical notes (+3 more)

### Community 182 - "Condition-Based Waiting"
Cohesion: 0.20
Nodes (9): Common Mistakes, Condition-Based Waiting, Core Pattern, Implementation, Overview, Quick Patterns, Real-World Impact, When Arbitrary Timeout IS Correct (+1 more)

### Community 183 - "Verification Before Completion"
Cohesion: 0.20
Nodes (9): Common Failures, Key Patterns, Overview, Rationalization Prevention, Red Flags - STOP, The Gate Function, The Iron Law, Verification Before Completion (+1 more)

### Community 184 - "Skill structure"
Cohesion: 0.20
Nodes (10): Avoid deeply nested references, Naming conventions, Pattern 1: High-level guide with references, Pattern 2: Domain-specific organization, Pattern 3: Conditional details, Progressive disclosure patterns, Skill structure, Structure longer reference files with table of contents (+2 more)

### Community 185 - "Iron Man JARVIS UI — Avatar Redesign + App Theme"
Cohesion: 0.17
Nodes (11): Composition (300×300 canvas, center 150,150), Iron Man JARVIS UI — Avatar Redesign + App Theme, Out of scope, Overview, Palette, Phase behavior, Requirements (from brainstorming), Screens (+3 more)

### Community 186 - "helper.js"
Cohesion: 0.42
Nodes (7): connect(), nextReconnectDelay(), reloadAfterRecovery(), sessionKey(), setStatus(), showTombstone(), websocketUrl()

### Community 187 - "OpenCode Tool Mapping"
Cohesion: 0.22
Nodes (6): Environment Detection, Model Selection Note, OpenCode Tool Mapping, Tool Mapping, Windows / PowerShell Notes, Worktrees

### Community 188 - "Skill authoring best practices"
Cohesion: 0.22
Nodes (9): Avoid time-sensitive information, Common patterns, Content guidelines, Implement feedback loops, Skill authoring best practices, Template pattern, Use consistent terminology, Use workflows for complex tasks (+1 more)

### Community 189 - "render-graphs.js"
Cohesion: 0.33
Nodes (8): combineGraphs(), { execSync }, extractDotBlocks(), extractGraphBody(), fs, main(), path, renderToSvg()

### Community 190 - "Global Constraints"
Cohesion: 0.22
Nodes (8): Global Constraints, Iron Man JARVIS Avatar Redesign + App Theme — Implementation Plan, Task 1: Create theme token file, Task 2: Rebuild the avatar as an arc-reactor HUD, Task 3: Restyle Home screen chrome, Task 4: Token-swap const-block screens, Task 5: Token-swap inline-literal screens, Task 6: Final verification

### Community 191 - "Brainstorming Ideas Into Designs"
Cohesion: 0.25
Nodes (7): After the Design, Anti-Pattern: "This Is Too Simple To Need A Design", Brainstorming Ideas Into Designs, Checklist, Process Flow, The Process, Visual Companion

### Community 192 - "ThermalLoggerService"
Cohesion: 0.18
Nodes (6): IO_COUNTERS, JOBOBJECT_BASIC_LIMIT_INFORMATION, JOBOBJECT_EXTENDED_LIMIT_INFORMATION, _Kernel32, Lifecycle-managed thermal logger: exactly one instance, tied to the backend…, ThermalLoggerService

### Community 193 - "using-superpowers/SKILL.md"
Cohesion: 0.29
Nodes (6): Naming, Platform Adaptation, Red Flags, Skill Priority, The Rule, User Instructions

### Community 194 - "REFACTOR Phase: Close Loopholes (Stay Green)"
Cohesion: 0.29
Nodes (7): 1. Explicit Negation in Rules, 2. Entry in Rationalization Table, 3. Red Flag Entry, 4. Update description, Plugging Each Hole, Re-verify After Refactoring, REFACTOR Phase: Close Loopholes (Stay Green)

### Community 195 - "Skill Discovery Optimization (SDO)"
Cohesion: 0.33
Nodes (6): 1. Rich Description Field, 2. Keyword Coverage, 3. Descriptive Naming, 4. Token Efficiency (Critical), 5. Cross-Referencing Other Skills, Skill Discovery Optimization (SDO)

### Community 196 - "Bulletproofing Skills Against Rationalization"
Cohesion: 0.33
Nodes (6): Address "Spirit vs Letter" Arguments, Build Rationalization Table, Bulletproofing Skills Against Rationalization, Close Every Loophole Explicitly, Create Red Flags List, Update SDO for Violation Symptoms

### Community 197 - "anthropic-best-practices.md"
Cohesion: 0.40
Nodes (4): [Analysis Title], Executive summary, Key findings, Recommendations

### Community 198 - "Anti-Patterns"
Cohesion: 0.40
Nodes (5): Anti-Patterns, ❌ Code in Flowcharts, ❌ Generic Labels, ❌ Multi-Language Dilution, ❌ Narrative Example

### Community 199 - "Testing All Skill Types"
Cohesion: 0.40
Nodes (5): Discipline-Enforcing Skills (rules/requirements), Pattern Skills (mental models), Reference Skills (documentation/APIs), Technique Skills (how-to guides), Testing All Skill Types

### Community 200 - "RED-GREEN-REFACTOR for Skills"
Cohesion: 0.40
Nodes (5): GREEN: Write Minimal Skill, Micro-Test Wording Before Full Scenarios, RED-GREEN-REFACTOR for Skills, RED: Write Failing Test (Baseline), REFACTOR: Close Loopholes

### Community 201 - "VERIFY GREEN: Pressure Testing"
Cohesion: 0.40
Nodes (5): Key Elements of Good Scenarios, Pressure Types, Testing Setup, VERIFY GREEN: Pressure Testing, Writing Pressure Scenarios

### Community 203 - "broadcast"
Cohesion: 0.25
Nodes (9): broadcast(), _broadcast_voice_alert(), handle_device_heartbeat(), handle_device_register(), handle_device_status_update(), handle_screen_start(), handle_screen_stop(), _monitoring_alert_callback() (+1 more)

### Community 204 - "Checklist for effective Skills"
Cohesion: 0.50
Nodes (4): Checklist for effective Skills, Code and scripts, Core quality, Testing

### Community 205 - "Core principles"
Cohesion: 0.50
Nodes (4): Concise is key, Core principles, Set appropriate degrees of freedom, Test with all models you plan to use

### Community 206 - "File Organization"
Cohesion: 0.50
Nodes (4): File Organization, Self-Contained Skill, Skill with Heavy Reference, Skill with Reusable Tool

### Community 207 - "Skill Types"
Cohesion: 0.50
Nodes (4): Pattern, Reference, Skill Types, Technique

### Community 208 - "Example: TDD Skill Bulletproofing"
Cohesion: 0.50
Nodes (4): Example: TDD Skill Bulletproofing, Initial Test (Failed), Iteration 1 - Add Counter, Iteration 2 - Add Foundational Principle

### Community 217 - "_SpecsCheckScreenState"
Cohesion: 0.40
Nodes (5): SpecsCheckScreen, _SpecsCheckScreenState, AvatarWidget, _AvatarWidgetState, TickerProviderStateMixin

### Community 218 - "system_service.dart"
Cohesion: 0.22
Nodes (8): applyTier, baseUrl, checkBackend, getAvailableModels, getConfig, getSpecs, SystemService, updateConfig

### Community 219 - "handle_voice_mode_start"
Cohesion: 0.50
Nodes (4): _build_system_prompt(), handle_text_message(), handle_voice_mode_start(), Build system prompt with browser state and RAG context.

### Community 220 - "Evaluation and iteration"
Cohesion: 0.50
Nodes (4): Build evaluations first, Develop Skills iteratively with the agent, Evaluation and iteration, Observe how agents navigate Skills

## Knowledge Gaps
- **1804 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `crypto`, `http`, `fs` (+1799 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WearableDevice` connect `WearableService` to `websocket.py`, `wearable_screen.dart`, `broadcast`, `health_screen.dart`, `vision.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `SystemCommandService` connect `SystemCommandService` to `DateTime`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `VoiceSession` (e.g. with `ClientInfo` and `FakeProfile`) actually correct?**
  _`VoiceSession` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `crypto` to the rest of the system?**
  _1804 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `websocket.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09706083390293917 - nodes in this community are weakly interconnected._
- **Should `voice_service.dart` be split into smaller, more focused modules?**
  _Cohesion score 0.031746031746031744 - nodes in this community are weakly interconnected._
- **Should `index.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.05875251509054326 - nodes in this community are weakly interconnected._