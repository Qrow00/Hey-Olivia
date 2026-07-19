import 'dart:convert';
import 'package:http/http.dart' as http;

class PersonalityService {
  final String baseUrl;

  PersonalityService({this.baseUrl = 'http://localhost:8000'});

  Future<Map> getStatus() async {
    final response = await http.get(Uri.parse('$baseUrl/api/v1/personality'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return {};
  }

  Future<Map> updateStyle({
    double? formality,
    double? humor,
    double? verbosity,
    double? empathy,
    double? directness,
    double? enthusiasm,
  }) async {
    final body = <String, dynamic>{};
    if (formality != null) body['formality'] = formality;
    if (humor != null) body['humor'] = humor;
    if (verbosity != null) body['verbosity'] = verbosity;
    if (empathy != null) body['empathy'] = empathy;
    if (directness != null) body['directness'] = directness;
    if (enthusiasm != null) body['enthusiasm'] = enthusiasm;

    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/personality/style'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return jsonDecode(response.body);
  }

  Future<Map> setFeedback(String type) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/personality/feedback'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'type': type}),
    );
    return jsonDecode(response.body);
  }

  Future<Map> learnOpinion(String topic, String stance) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/personality/opinion'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'topic': topic, 'stance': stance}),
    );
    return jsonDecode(response.body);
  }

  Future<Map> setName(String name) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/personality/name'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name}),
    );
    return jsonDecode(response.body);
  }
}
