import 'dart:convert';
import 'package:http/http.dart' as http;

class VoiceProfileService {
  final String baseUrl;

  VoiceProfileService({this.baseUrl = 'http://localhost:8000'});

  Future<List> getProfiles() async {
    final response = await http.get(Uri.parse('$baseUrl/api/v1/voice-profiles'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body) ?? [];
    }
    return [];
  }

  Future<Map> switchProfile(String profileId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/voice-profiles/active'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'profile_id': profileId}),
    );
    return jsonDecode(response.body);
  }

  Future<Map> createProfile({
    required String id,
    required String name,
    required String voice,
    int rate = 0,
    int pitch = 0,
    String description = '',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/voice-profiles'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'id': id,
        'name': name,
        'voice': voice,
        'rate': rate,
        'pitch': pitch,
        'description': description,
      }),
    );
    return jsonDecode(response.body);
  }

  Future<Map> deleteProfile(String profileId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/v1/voice-profiles/$profileId'),
    );
    return jsonDecode(response.body);
  }
}
