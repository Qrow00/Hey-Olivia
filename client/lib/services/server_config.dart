import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

class ServerConfig {
  static ServerConfig? _instance;

  String baseUrl;
  String wsUrl;
  String? tailscaleIp;
  String? token;
  String? profileId;
  String? profileName;

  ServerConfig({
    required this.baseUrl,
    required this.wsUrl,
    this.tailscaleIp,
    this.token,
    this.profileId,
    this.profileName,
  });

  Map<String, dynamic> toJson() => {
        'baseUrl': baseUrl,
        'wsUrl': wsUrl,
        'tailscaleIp': tailscaleIp,
        if (token != null) 'token': token,
        if (profileId != null) 'profileId': profileId,
        if (profileName != null) 'profileName': profileName,
      };

  factory ServerConfig.fromJson(Map<String, dynamic> json) => ServerConfig(
        baseUrl: json['baseUrl'] as String,
        wsUrl: json['wsUrl'] as String,
        tailscaleIp: json['tailscaleIp'] as String?,
        token: json['token'] as String?,
        profileId: json['profileId'] as String?,
        profileName: json['profileName'] as String?,
      );

  static String wsFromBase(String base) =>
      base.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://') +
      '/ws';

  static Future<String> _getConfigPath() async {
    final dir = await getApplicationDocumentsDirectory();
    return '${dir.path}/server_config.json';
  }

  static Future<ServerConfig?> load() async {
    final path = await _getConfigPath();
    final file = File(path);
    if (!await file.exists()) return null;
    try {
      final data = json.decode(await file.readAsString());
      return ServerConfig.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  Future<void> save() async {
    final path = await ServerConfig._getConfigPath();
    final file = File(path);
    await file.writeAsString(json.encode(toJson()));
  }

  static Future<bool> testConnection(String url) async {
    try {
      final response = await http
          .get(Uri.parse('$url/api/v1/system/health'))
          .timeout(Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<String?> discoverViaTailscan() async {
    try {
      final response = await http
          .get(Uri.parse('http://100.100.100.100:8000/api/v1/system/health'))
          .timeout(Duration(seconds: 3));
      if (response.statusCode == 200) return 'http://100.100.100.100:8000';
    } catch (_) {}
    return null;
  }

  static Future<ServerConfig?> resolve() async {
    final saved = await load();
    if (saved != null) {
      if (await testConnection(saved.baseUrl)) return saved;
      if (saved.tailscaleIp != null) {
        final tsUrl = 'http://${saved.tailscaleIp}:8000';
        if (await testConnection(tsUrl)) {
          saved.baseUrl = tsUrl;
          saved.wsUrl = wsFromBase(tsUrl);
          await saved.save();
          return saved;
        }
      }
    }
    final discovered = await discoverViaTailscan();
    if (discovered != null) {
      final config = ServerConfig(
        baseUrl: discovered,
        wsUrl: wsFromBase(discovered),
      );
      await config.save();
      return config;
    }
    return null;
  }
}
