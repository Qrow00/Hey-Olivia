import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/smart_device.dart';
import 'websocket_service.dart';

class SmartHomeService {
  final WebSocketService _webSocketService;
  final String baseUrl;
  final StreamController<SmartDevice> _deviceController =
      StreamController<SmartDevice>.broadcast();

  Stream<SmartDevice> get deviceUpdates => _deviceController.stream;

  List<SmartDevice> _devices = [];
  List<SmartDevice> get allDevices => _devices;

  SmartHomeService(this._webSocketService, {this.baseUrl = 'http://localhost:8000'}) {
    _setupWebSocketListeners();
  }

  void _setupWebSocketListeners() {
    _webSocketService.messages.listen((message) {
      if (message['type'] == 'smart_home_update') {
        final device = SmartDevice.fromJson(message['device']);
        _updateDevice(device);
      }
    });
  }

  void _updateDevice(SmartDevice updated) {
    for (var i = 0; i < _devices.length; i++) {
      if (_devices[i].id == updated.id) {
        _devices[i] = updated;
        _deviceController.add(updated);
        break;
      }
    }
  }

  Future<List<SmartDevice>> fetchDevices() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/smart-home'));
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        _devices = data.map((d) => SmartDevice.fromJson(d)).toList();
        return _devices;
      }
    } catch (e) {
      print('Error fetching smart devices: $e');
    }
    return [];
  }

  Future<List<String>> fetchRooms() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/smart-home/rooms'));
      if (response.statusCode == 200) {
        return List<String>.from(json.decode(response.body));
      }
    } catch (e) {
      print('Error fetching rooms: $e');
    }
    return [];
  }

  Future<SmartDevice?> addDevice({
    required String name,
    required String type,
    required String protocol,
    String ip = '',
    String topic = '',
    String room = '',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/smart-home'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'name': name,
          'type': type,
          'protocol': protocol,
          'ip': ip,
          'topic': topic,
          'room': room,
        }),
      );
      if (response.statusCode == 200) {
        await fetchDevices();
        return _devices.isNotEmpty ? _devices.last : null;
      }
    } catch (e) {
      print('Error adding device: $e');
    }
    return null;
  }

  Future<void> removeDevice(String deviceId) async {
    try {
      await http.delete(Uri.parse('$baseUrl/api/v1/smart-home/$deviceId'));
      _devices.removeWhere((d) => d.id == deviceId);
    } catch (e) {
      print('Error removing device: $e');
    }
  }

  Future<void> turnOn(String deviceId) async {
    await _control(deviceId, 'on');
  }

  Future<void> turnOff(String deviceId) async {
    await _control(deviceId, 'off');
  }

  Future<void> toggle(String deviceId) async {
    await _control(deviceId, 'toggle');
  }

  Future<void> setBrightness(String deviceId, int brightness) async {
    await _control(deviceId, 'set_brightness', {'brightness': brightness});
  }

  Future<void> setColor(String deviceId, String color) async {
    await _control(deviceId, 'set_color', {'color': color});
  }

  Future<void> setTemperature(String deviceId, double temperature) async {
    await _control(deviceId, 'set_temperature', {'temperature': temperature});
  }

  Future<void> _control(String deviceId, String action, [Map<String, dynamic>? params]) async {
    try {
      await http.post(
        Uri.parse('$baseUrl/api/v1/smart-home/$deviceId/control'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'action': action,
          'params': params ?? {},
        }),
      );

      for (var device in _devices) {
        if (device.id == deviceId) {
          SmartDevice updated;
          switch (action) {
            case 'on':
              updated = SmartDevice(
                id: device.id, name: device.name, type: device.type,
                protocol: device.protocol, ip: device.ip, topic: device.topic,
                room: device.room, isOnline: device.isOnline, isOn: true,
                brightness: device.brightness, color: device.color,
                temperature: device.temperature, humidity: device.humidity,
                battery: device.battery, state: device.state,
                capabilities: device.capabilities,
              );
              break;
            case 'off':
              updated = SmartDevice(
                id: device.id, name: device.name, type: device.type,
                protocol: device.protocol, ip: device.ip, topic: device.topic,
                room: device.room, isOnline: device.isOnline, isOn: false,
                brightness: device.brightness, color: device.color,
                temperature: device.temperature, humidity: device.humidity,
                battery: device.battery, state: device.state,
                capabilities: device.capabilities,
              );
              break;
            case 'toggle':
              updated = SmartDevice(
                id: device.id, name: device.name, type: device.type,
                protocol: device.protocol, ip: device.ip, topic: device.topic,
                room: device.room, isOnline: device.isOnline, isOn: !device.isOn,
                brightness: device.brightness, color: device.color,
                temperature: device.temperature, humidity: device.humidity,
                battery: device.battery, state: device.state,
                capabilities: device.capabilities,
              );
              break;
            case 'set_brightness':
              updated = SmartDevice(
                id: device.id, name: device.name, type: device.type,
                protocol: device.protocol, ip: device.ip, topic: device.topic,
                room: device.room, isOnline: device.isOnline, isOn: device.isOn,
                brightness: params?['brightness'] ?? device.brightness,
                color: device.color, temperature: device.temperature,
                humidity: device.humidity, battery: device.battery,
                state: device.state, capabilities: device.capabilities,
              );
              break;
            case 'set_color':
              updated = SmartDevice(
                id: device.id, name: device.name, type: device.type,
                protocol: device.protocol, ip: device.ip, topic: device.topic,
                room: device.room, isOnline: device.isOnline, isOn: device.isOn,
                brightness: device.brightness,
                color: params?['color'] ?? device.color,
                temperature: device.temperature, humidity: device.humidity,
                battery: device.battery, state: device.state,
                capabilities: device.capabilities,
              );
              break;
            default:
              updated = device;
          }
          _updateDevice(updated);
          break;
        }
      }
    } catch (e) {
      print('Error controlling device: $e');
    }
  }

  Future<void> connectMQTT({
    required String broker,
    int port = 1883,
    String username = '',
    String password = '',
  }) async {
    try {
      await http.post(
        Uri.parse('$baseUrl/api/v1/smart-home/mqtt/connect'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'broker': broker,
          'port': port,
          'username': username,
          'password': password,
        }),
      );
    } catch (e) {
      print('Error connecting MQTT: $e');
    }
  }

  void dispose() {
    _deviceController.close();
  }
}
