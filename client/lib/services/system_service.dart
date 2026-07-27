import 'dart:convert';
import 'package:http/http.dart' as http;

class SystemService {
  final String baseUrl;

  SystemService({required this.baseUrl});

  Future<Map<String, dynamic>?> getSpecs() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/system/specs'),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}
    return null;
  }

  Future<Map<String, dynamic>?> getConfig() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/system/config'),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}
    return null;
  }

  Future<Map<String, dynamic>?> applyTier(String tier) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/system/config/apply?tier=$tier'),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}
    return null;
  }

  Future<Map<String, dynamic>?> updateConfig(Map<String, dynamic> updates) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/system/config'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(updates),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}
    return null;
  }

  Future<Map<String, dynamic>?> getAvailableModels() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/system/models'),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}
    return null;
  }

  Future<bool> checkBackend() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/'),
      ).timeout(Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
