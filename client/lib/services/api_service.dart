import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  final String baseUrl;

  ApiService({required this.baseUrl});

  Future<List<dynamic>> getDevices() async {
    final response = await http.get(Uri.parse('$baseUrl/api/devices'));
    return json.decode(response.body);
  }

  Future<List<dynamic>> getConversations(String userId) async {
    final response =
        await http.get(Uri.parse('$baseUrl/api/conversations?user_id=$userId'));
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> settings) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/settings'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(settings),
    );
    return json.decode(response.body);
  }

  Future<List<dynamic>> getCommands() async {
    final response = await http.get(Uri.parse('$baseUrl/api/commands'));
    return json.decode(response.body);
  }
}
