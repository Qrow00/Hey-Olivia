import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/wearable.dart';
import 'websocket_service.dart';

class WearableService {
  final WebSocketService _webSocketService;
  final String baseUrl;
  final StreamController<WearableDevice> _deviceController =
      StreamController<WearableDevice>.broadcast();
  final StreamController<HealthMetricData> _healthController =
      StreamController<HealthMetricData>.broadcast();
  final StreamController<HealthAlert> _alertController =
      StreamController<HealthAlert>.broadcast();

  Stream<WearableDevice> get devices => _deviceController.stream;
  Stream<HealthMetricData> get healthUpdates => _healthController.stream;
  Stream<HealthAlert> get alerts => _alertController.stream;

  List<WearableDevice> _devices = [];
  List<WearableDevice> get allDevices => _devices;

  WearableService(this._webSocketService, {this.baseUrl = 'http://localhost:8000'}) {
    _setupWebSocketListeners();
  }

  void _setupWebSocketListeners() {
    _webSocketService.messages.listen((message) {
      final type = message['type'];

      if (type == 'wearable_health_data') {
        final metric = HealthMetricData.fromJson({
          'current': message['value'],
          'unit': message['unit'],
          'timestamp': message['timestamp'],
        });
        _healthController.add(metric);

        _updateDeviceHealth(message['device_id'], message['metric'], metric);
      }
    });
  }

  void _updateDeviceHealth(String deviceId, String metricName, HealthMetricData data) {
    for (var i = 0; i < _devices.length; i++) {
      if (_devices[i].id == deviceId) {
        final device = _devices[i];
        final summary = device.healthSummary ?? HealthSummary();

        HealthSummary updatedSummary;
        switch (metricName) {
          case 'heart_rate':
            updatedSummary = HealthSummary(
              heartRate: data, spo2: summary.spo2, steps: summary.steps,
              sleep: summary.sleep, calories: summary.calories, stress: summary.stress,
              bloodPressure: summary.bloodPressure, bodyTemperature: summary.bodyTemperature,
            );
            break;
          case 'spo2':
            updatedSummary = HealthSummary(
              heartRate: summary.heartRate, spo2: data, steps: summary.steps,
              sleep: summary.sleep, calories: summary.calories, stress: summary.stress,
              bloodPressure: summary.bloodPressure, bodyTemperature: summary.bodyTemperature,
            );
            break;
          case 'steps':
            updatedSummary = HealthSummary(
              heartRate: summary.heartRate, spo2: summary.spo2, steps: data,
              sleep: summary.sleep, calories: summary.calories, stress: summary.stress,
              bloodPressure: summary.bloodPressure, bodyTemperature: summary.bodyTemperature,
            );
            break;
          case 'sleep':
            updatedSummary = HealthSummary(
              heartRate: summary.heartRate, spo2: summary.spo2, steps: summary.steps,
              sleep: data, calories: summary.calories, stress: summary.stress,
              bloodPressure: summary.bloodPressure, bodyTemperature: summary.bodyTemperature,
            );
            break;
          case 'calories':
            updatedSummary = HealthSummary(
              heartRate: summary.heartRate, spo2: summary.spo2, steps: summary.steps,
              sleep: summary.sleep, calories: data, stress: summary.stress,
              bloodPressure: summary.bloodPressure, bodyTemperature: summary.bodyTemperature,
            );
            break;
          case 'stress':
            updatedSummary = HealthSummary(
              heartRate: summary.heartRate, spo2: summary.spo2, steps: summary.steps,
              sleep: summary.sleep, calories: summary.calories, stress: data,
              bloodPressure: summary.bloodPressure, bodyTemperature: summary.bodyTemperature,
            );
            break;
          case 'blood_pressure':
            updatedSummary = HealthSummary(
              heartRate: summary.heartRate, spo2: summary.spo2, steps: summary.steps,
              sleep: summary.sleep, calories: summary.calories, stress: summary.stress,
              bloodPressure: data, bodyTemperature: summary.bodyTemperature,
            );
            break;
          case 'body_temperature':
            updatedSummary = HealthSummary(
              heartRate: summary.heartRate, spo2: summary.spo2, steps: summary.steps,
              sleep: summary.sleep, calories: summary.calories, stress: summary.stress,
              bloodPressure: summary.bloodPressure, bodyTemperature: data,
            );
            break;
          default:
            updatedSummary = summary;
        }

        _devices[i] = WearableDevice(
          id: device.id,
          name: device.name,
          type: device.type,
          platform: device.platform,
          isOnline: device.isOnline,
          battery: device.battery,
          firmwareVersion: device.firmwareVersion,
          lastSync: device.lastSync,
          healthSummary: updatedSummary,
        );
        _deviceController.add(_devices[i]);
        break;
      }
    }
  }

  Future<List<WearableDevice>> fetchDevices() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/wearables'));
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        _devices = data.map((d) => WearableDevice.fromJson(d)).toList();
        for (var device in _devices) {
          _deviceController.add(device);
        }
        return _devices;
      }
    } catch (e) {
      print('Error fetching wearables: $e');
    }
    return [];
  }

  Future<WearableDevice?> registerDevice({
    required String name,
    String type = 'smartwatch',
    String platform = 'android',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/wearables'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'name': name,
          'type': type,
          'platform': platform,
        }),
      );
      if (response.statusCode == 200) {
        await fetchDevices();
        return _devices.isNotEmpty ? _devices.last : null;
      }
    } catch (e) {
      print('Error registering wearable: $e');
    }
    return null;
  }

  Future<void> removeDevice(String deviceId) async {
    try {
      await http.delete(Uri.parse('$baseUrl/api/v1/wearables/$deviceId'));
      _devices.removeWhere((d) => d.id == deviceId);
      _deviceController.add(WearableDevice(id: '', name: '', type: '', platform: ''));
    } catch (e) {
      print('Error removing wearable: $e');
    }
  }

  Future<void> updateHealth({
    required String deviceId,
    required String metric,
    required double value,
    String unit = '',
  }) async {
    try {
      await http.post(
        Uri.parse('$baseUrl/api/v1/wearables/$deviceId/health'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'metric': metric,
          'value': value,
          'unit': unit,
        }),
      );

      _webSocketService.send({
        'type': 'wearable_health_update',
        'device_id': deviceId,
        'metric': metric,
        'value': value,
        'unit': unit,
      });
    } catch (e) {
      print('Error updating health: $e');
    }
  }

  Future<HealthSummary?> getHealthSummary(String deviceId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/wearables/$deviceId/health'),
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return HealthSummary.fromJson(data['health']);
      }
    } catch (e) {
      print('Error fetching health summary: $e');
    }
    return null;
  }

  Future<List<Map<String, dynamic>>> getHealthHistory(
    String deviceId, {
    String? metric,
    int limit = 50,
  }) async {
    try {
      var url = '$baseUrl/api/v1/wearables/$deviceId/health/history?limit=$limit';
      if (metric != null) url += '&metric=$metric';

      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<Map<String, dynamic>>.from(data['history']);
      }
    } catch (e) {
      print('Error fetching health history: $e');
    }
    return [];
  }

  void subscribeToUpdates(String deviceId, {List<String> metrics = const ['heart_rate', 'spo2', 'steps', 'sleep']}) {
    _webSocketService.send({
      'type': 'wearable_subscribe',
      'device_id': deviceId,
      'metrics': metrics,
    });
  }

  void unsubscribeFromUpdates() {
    _webSocketService.send({
      'type': 'wearable_unsubscribe',
    });
  }

  void dispose() {
    _deviceController.close();
    _healthController.close();
    _alertController.close();
  }
}
