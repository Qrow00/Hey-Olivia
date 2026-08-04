import 'dart:convert';
import 'package:http/http.dart' as http;
import 'server_config.dart';

class SettingsService {
  final ServerConfig _config;
  Map<String, dynamic> _settings = {};
  bool _loaded = false;

  SettingsService(this._config);

  Map<String, dynamic> get all => Map.from(_settings);
  bool get isLoaded => _loaded;

  Map<String, dynamic> _voice() =>
      Map<String, dynamic>.from(_settings['voice'] as Map? ?? {});
  Map<String, dynamic> _ui() =>
      Map<String, dynamic>.from(_settings['ui'] as Map? ?? {});
  Map<String, dynamic> _health() =>
      Map<String, dynamic>.from(_settings['health'] as Map? ?? {});
  Map<String, dynamic> _smartHome() =>
      Map<String, dynamic>.from(_settings['smart_home'] as Map? ?? {});

  bool get wakeWordEnabled => _voice()['wake_word_enabled'] as bool? ?? true;
  double get wakeWordSensitivity =>
      (_voice()['wake_word_sensitivity'] as num?)?.toDouble() ?? 0.5;
  String get ttsVoice => _voice()['tts_voice'] as String? ?? 'en-US-GuyNeural';
  String get voiceProfile => _voice()['voice_profile'] as String? ?? 'jarvis';
  String get llmModel => _voice()['llm_model'] as String? ?? 'llama3.2';
  bool get pushToTalk => _voice()['push_to_talk'] as bool? ?? false;

  bool get darkMode => _ui()['dark_mode'] as bool? ?? true;
  bool get notificationsEnabled =>
      _ui()['notifications_enabled'] as bool? ?? true;

  bool get healthAlertsEnabled =>
      _health()['alerts_enabled'] as bool? ?? false;
  bool get heartRateAlerts =>
      _health()['heart_rate_alerts'] as bool? ?? true;
  bool get spo2Alerts => _health()['spo2_alerts'] as bool? ?? true;

  String get mqttBroker =>
      _smartHome()['mqtt_broker'] as String? ?? '';
  int get mqttPort => (_smartHome()['mqtt_port'] as num?)?.toInt() ?? 1883;
  String get mqttUsername =>
      _smartHome()['mqtt_username'] as String? ?? '';
  String get mqttPassword =>
      _smartHome()['mqtt_password'] as String? ?? '';

  Map<String, String> get _authHeaders => {
    if (_config.token != null) 'Authorization': 'Bearer ${_config.token}',
    'Content-Type': 'application/json',
  };

  Future<void> fetch() async {
    final response = await http
        .get(Uri.parse('${_config.baseUrl}/api/v1/settings'), headers: _authHeaders)
        .timeout(Duration(seconds: 10));
    if (response.statusCode == 200) {
      _settings = json.decode(response.body) as Map<String, dynamic>;
      _loaded = true;
    } else {
      throw Exception('Failed to fetch settings: ${response.statusCode}');
    }
  }

  Future<void> save() async {
    final response = await http
        .put(
          Uri.parse('${_config.baseUrl}/api/v1/settings'),
          headers: _authHeaders,
          body: json.encode(_settings),
        )
        .timeout(Duration(seconds: 10));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      _settings = data['settings'] as Map<String, dynamic>? ?? _settings;
    } else {
      throw Exception('Failed to save settings: ${response.statusCode}');
    }
  }

  Future<void> patch(Map<String, dynamic> partial) async {
    final response = await http
        .patch(
          Uri.parse('${_config.baseUrl}/api/v1/settings'),
          headers: _authHeaders,
          body: json.encode(partial),
        )
        .timeout(Duration(seconds: 10));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      _settings = data['settings'] as Map<String, dynamic>? ?? _settings;
    } else {
      throw Exception('Failed to patch settings: ${response.statusCode}');
    }
  }
}
