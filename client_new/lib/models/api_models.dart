/// VoiceChunk - Represents a streaming audio chunk from the client.
///
/// Sent from Flutter client to backend via WebSocket.
/// Base64-encoded PCM16 audio, 16kHz sample rate, 80ms chunks.
class VoiceChunk {
  final String data; // base64 encoded audio
  final int sampleRate; // 16000
  final int timestamp; // milliseconds

  VoiceChunk({
    required this.data,
    required this.sampleRate,
    required this.timestamp,
  });

  /// Convert from Map (for JSON deserialization from WebSocket)
  factory VoiceChunk.fromMap(Map<String, dynamic> map) {
    return VoiceChunk(
      data: map['data'] as String,
      sampleRate: map['sampleRate'] as int? ?? 16000,
      timestamp: map['timestamp'] as int? ?? 0,
    );
  }

  /// Convert to Map (for JSON serialization to WebSocket)
  Map<String, dynamic> toMap() {
    return {
      'data': data,
      'sampleRate': sampleRate,
      'timestamp': timestamp,
    };
  }
}

/// CommandResult - Result of command execution on the backend.
///
/// Sent from backend to Flutter client after dispatch.
class CommandResult {
  final bool success;
  final String resultText; // Human-readable result description
  final String? handler; // Name of handler that executed, or null
  final String? commandType; // 'regex', 'llm_json', or 'chat'

  CommandResult({
    required this.success,
    required this.resultText,
    this.handler,
    this.commandType,
  });

  /// Convert from Map
  factory CommandResult.fromMap(Map<String, dynamic> map) {
    return CommandResult(
      success: map['success'] as bool? ?? false,
      resultText: map['resultText'] as String? ?? 'Unknown result',
      handler: map['handler'] as String?,
      commandType: map['commandType'] as String?,
    );
  }

  /// Convert to Map
  Map<String, dynamic> toMap() {
    return {
      'success': success,
      'resultText': resultText,
      'handler': handler,
      'commandType': commandType,
    };
  }
}

/// AvatarState - Enum-like class for avatar visual state.
enum AvatarState {
  idle,
  listening,
  thinking,
  speaking,
  error;

  /// String representation
  String get value {
    switch (this) {
      case AvatarState.idle:
        return 'idle';
      case AvatarState.listening:
        return 'listening';
      case AvatarState.thinking:
        return 'thinking';
      case AvatarState.speaking:
        return 'speaking';
      case AvatarState.error:
        return 'error';
    }
  }

  /// From string (for WebSocket deserialization)
  factory AvatarState.fromString(String value) {
    switch (value.toLowerCase()) {
      case 'idle':
        return AvatarState.idle;
      case 'listening':
        return AvatarState.listening;
      case 'thinking':
        return AvatarState.thinking;
      case 'speaking':
        return AvatarState.speaking;
      case 'error':
        return AvatarState.error;
      default:
        return AvatarState.idle;
    }
  }
}

/// JarvisResponse - Full response from backend to Flutter client.
class JarvisResponse {
  final String text; // Response text to display
  final String audioBase64; // Base64-encoded audio for TTS playback
  final AvatarState avatarState; // Avatar state for UI update

  JarvisResponse({
    required this.text,
    required this.audioBase64,
    required this.avatarState,
  });

  /// Convert from Map
  factory JarvisResponse.fromMap(Map<String, dynamic> map) {
    return JarvisResponse(
      text: map['text'] as String? ?? '',
      audioBase64: map['audioBase64'] as String? ?? '',
      avatarState: AvatarState.fromString(map['avatarState'] as String? ?? 'idle'),
    );
  }

  /// Convert to Map
  Map<String, dynamic> toMap() {
    return {
      'text': text,
      'audioBase64': audioBase64,
      'avatarState': avatarState.value,
    };
  }
}

/// ProfileSettings - Per-profile configuration.
class ProfileSettings {
  final String profile; // Profile name
  final String voice; // Selected voice: 'Jarvis', 'Friday', 'Edith', 'Tobby', 'Karen'
  final Map<String, dynamic> ui; // UI preferences (theme, etc.)
  final Map<String, dynamic> health; // Health metrics settings
  final Map<String, dynamic> smartHome; // Smart home settings

  ProfileSettings({
    required this.profile,
    required this.voice,
    required this.ui,
    required this.health,
    required this.smartHome,
  });

  /// Convert from Map
  factory ProfileSettings.fromMap(Map<String, dynamic> map) {
    return ProfileSettings(
      profile: map['profile'] as String? ?? 'default',
      voice: map['voice'] as String? ?? 'Jarvis',
      ui: map['ui'] as Map<String, dynamic>? ?? {},
      health: map['health'] as Map<String, dynamic>? ?? {},
      smartHome: map['smartHome'] as Map<String, dynamic>? ?? {},
    );
  }

  /// Convert to Map
  Map<String, dynamic> toMap() {
    return {
      'profile': profile,
      'voice': voice,
      'ui': ui,
      'health': health,
      'smartHome': smartHome,
    };
  }
}