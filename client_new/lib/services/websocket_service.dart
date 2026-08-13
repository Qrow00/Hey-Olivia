import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:path_provider/path_provider.dart';
import 'models/api_models.dart';

/// WebSocket service for J.A.R.V.I.S. V3 communication.
/// Handles all typed WebSocket message contracts.
class JarvisWebSocketService {
  final String _serverUrl;
  final String? _token;
  WebSocketChannel? _channel;
  final _messageStreamController = StreamController<dynamic>.broadcast();
  final _profileSettings = ProfileSettings(
    profile: 'default',
    voice: 'Jarvis',
    ui: {'theme': 'dark'},
    health: {'units': 'metric'},
    smartHome: {'enabled': false},
  );

  /// Stream of all incoming messages from backend
  Stream<dynamic> get messageStream => _messageStreamController.stream;

  /// Current profile settings
  ProfileSettings get profileSettings => _profileSettings;

  JarvisWebSocketService({String? serverUrl, String? token}) {
    _serverUrl = serverUrl ?? 'ws://localhost:8000/ws';
    _token = token;
  }

  /// Connect to the J.A.R.V.I.S. backend WebSocket server
  Future<void> connect() async {
    // Build WebSocket URL with optional token
    String url = _serverUrl;
    if (_token != null && _token!.isNotEmpty) {
      url += '?token=$_token';
    }

    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _channel!.stream.listen(_handleIncomingMessage,
          onError: (error) => print('WebSocket error: $error'),
      onDone: () => print('WebSocket connection closed'));
      print('Connected to J.A.R.V.I.S. V3 WebSocket: $url');
    } catch (e) {
      print('Failed to connect to WebSocket: $e');
      rethrow;
    }
  }

  /// Handle incoming WebSocket messages
  void _handleIncomingMessage(dynamic message) {
    // Convert String message to Map if needed
    if (message is! Map<String, dynamic>) {
      try {
        message = jsonDecode(message) as Map<String, dynamic>;
      } catch (e) {
        print('Failed to parse WebSocket message: $e');
        return;
      }
    }

    // Dispatch based on message type
    final type = message['type'] as String? ?? '';

    switch (type) {
      case 'voice_status':
        _handleVoiceStatus(message);
        break;
      case 'command_result':
        _handleCommandResult(message);
        break;
      case 'response':
        _handleResponse(message);
        break;
      case 'avatar_state':
        _handleAvatarState(message);
        break;
      case 'settings_updated':
        _handleSettingsUpdated(message);
        break;
      case 'plugin_status':
        _handlePluginStatus(message);
        break;
      case 'knowledge_results':
        _handleKnowledgeResults(message);
        break;
      case 'profile_switched':
        _handleProfileSwitched(message);
        break;
      case 'error':
        _handleError(message);
        break;
      default:
        print('Unknown WebSocket message type: $type');
    }
  }

  /// Handle voice_status messages from backend
  void _handleVoiceStatus(Map<String, dynamic> message) {
    final isListening = message['is_listening'] as bool?;
    final wakeDetected = message['wake_detected'] as bool?;
    // TODO: Update UI state for listening/wake detection
    print('[WebSocket] Voice status: listening=$isListening, wake=$wakeDetected');
  }

  /// Handle command_result messages from backend
  void _handleCommandResult(Map<String, dynamic> message) {
    final result = CommandResult.fromMap(message);
    // TODO: Update UI with command result
    print('[WebSocket] Command result: success=${result.success}, text=${result.resultText}');
  }

  /// Handle response messages (text + audio from TTS)
  void _handleResponse(Map<String, dynamic> message) {
    final response = JarvisResponse.fromMap(message);
    // TODO: Play audio, update text display, update avatar state
    print('[WebSocket] Response: text=${response.text}, avatar=${response.avatarState.value}');
  }

  /// Handle avatar_state messages
  void _handleAvatarState(Map<String, dynamic> message) {
    final state = AvatarState.fromString(message['state'] as String? ?? 'idle');
    // TODO: Update avatar widget state
    print('[WebSocket] Avatar state: $state');
  }

  /// Handle settings_updated messages
  void _handleSettingsUpdated(Map<String, dynamic> message) {
    // Update local profile settings
    final profile = message['profile'] as String?;
    if (profile != null) {
      _profileSettings.profile = profile;
    }
    final settings = message['settings'] as Map<String, dynamic>?;
    if (settings != null) {
      _profileSettings.ui = settings['ui'] as Map<String, dynamic>? ?? {};
      _profileSettings.health = settings['health'] as Map<String, dynamic>? ?? {};
      _profileSettings.smartHome = settings['smartHome'] as Map<String, dynamic>? ?? {};
    }
    print('[WebSocket] Settings updated for profile: ${_profileSettings.profile}');
  }

  /// Handle plugin_status messages
  void _handlePluginStatus(Map<String, dynamic> message) {
    final name = message['name'] as String? ?? '';
    final enabled = message['enabled'] as bool? ?? false;
    // TODO: Update plugin status UI
    print('[WebSocket] Plugin status: $name enabled=$enabled');
  }

  /// Handle knowledge_results messages
  void _handleKnowledgeResults(Map<String, dynamic> message) {
    final results = message['results'] as List?;
    print('[WebSocket] Knowledge results: ${results?.length ?? 0} results');
  }

  /// Handle profile_switched messages
  void _handleProfileSwitched(Map<String, dynamic> message) {
    final profile = message['profile'] as String? ?? 'default';
    print('[WebSocket] Profile switched to: $profile');
  }

  /// Handle error messages
  void _handleError(Map<String, dynamic> message) {
    final code = message['code'] as String? ?? 'unknown';
    final messageText = message['message'] as String? ?? 'Unknown error';
    print('[WebSocket] Error [$code]: $messageText');
  }

  /// Send voice chunk (base64 audio) to backend
  Future<void> sendVoiceChunk(String base64Audio, {int sampleRate = 16000, required int timestamp}) async {
    if (_channel == null || !_channel!.sink!.isClosed) {
      final chunk = {
        'type': 'voice_chunk',
        'data': base64Audio,
        'sampleRate': sampleRate,
        'timestamp': timestamp,
      };
      _channel!.sink!.add(jsonEncode(chunk));
    }
  }

  /// Send text command to backend (bypasses STT, goes directly to command dispatcher)
  Future<void> sendTextCommand(String text) async {
    if (_channel == null || !_channel!.sink!.isClosed) {
      final msg = {
        'type': 'voice_command',
        'text': text,
      };
      _channel!.sink!.add(jsonEncode(msg));
    }
  }

  /// Update profile settings
  Future<void> updateSettings(ProfileSettings settings) async {
    if (_channel == null || !_channel!.sink!.isClosed) {
      final msg = {
        'type': 'settings_update',
        'profile': settings.profile,
        'settings': {
          'voice': settings.voice,
          'ui': settings.ui,
          'health': settings.health,
          'smartHome': settings.smartHome,
        },
      };
      _channel!.sink!.add(jsonEncode(msg));
    }
  }

  /// Enable/disable a plugin at runtime
  Future<void> controlPlugin(String pluginName, bool enabled) async {
    if (_channel == null || !_channel!.sink!.isClosed) {
      final msg = {
        'type': 'plugin_control',
        'name': pluginName,
        'enabled': enabled,
      };
      _channel!.sink!.add(jsonEncode(msg));
    }
  }

  /// Switch active profile
  Future<void> switchProfile(String profileName) async {
    if (_channel == null || !_channel!.sink!.isClosed) {
      final msg = {
        'type': 'switch_profile',
        'profile': profileName,
      };
      _channel!.sink!.add(jsonEncode(msg));
    }
  }

  /// Request knowledge base search
  Future<void> searchKnowledge(String query) async {
    if (_channel == null || !_channel!.sink!.isClosed) {
      final msg = {
        'type': 'knowledge_search',
        'query': query,
      };
      _channel!.sink!.add(jsonEncode(msg));
    }
  }

  /// Dispose of WebSocket connection
  void dispose() {
    _channel?.sink!.close();
    _messageStreamController.close();
  }
}