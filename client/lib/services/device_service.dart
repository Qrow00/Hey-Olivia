import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/device.dart';
import 'websocket_service.dart';

class DeviceService {
  final WebSocketService _webSocketService;
  final String _baseUrl;
  final String? _token;

  final _devicesController = StreamController<List<Device>>.broadcast();
  final _deviceUpdateController = StreamController<Device>.broadcast();
  final _deviceEventController = StreamController<Map<String, dynamic>>.broadcast();

  Stream<List<Device>> get devices => _devicesController.stream;
  Stream<Device> get deviceUpdate => _deviceUpdateController.stream;
  Stream<Map<String, dynamic>> get deviceEvents => _deviceEventController.stream;
  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  List<Device> _devices = [];

  DeviceService(this._webSocketService, {required String baseUrl, String? token})
      : _baseUrl = baseUrl, _token = token {
    _webSocketService.messages.listen(_handleMessage);
  }

  void _handleMessage(Map<String, dynamic> message) {
    final type = message['type'];

    switch (type) {
      case 'device_connected':
      case 'device_heartbeat':
      case 'device_status_update':
        _handleDeviceEvent(message);
        break;
      case 'device_disconnected':
        _handleDeviceDisconnected(message);
        break;
    }

    _deviceEventController.add(message);
  }

  void _handleDeviceEvent(Map<String, dynamic> message) {
    final deviceId = message['device_id'];
    final index = _devices.indexWhere((d) => d.id == deviceId);

    if (index >= 0) {
      final device = _devices[index];
      _devices[index] = device.copyWith(
        status: message['status'] ?? device.status,
        battery: message['battery'] ?? device.battery,
        signal: message['signal'] ?? device.signal,
      );
      _deviceUpdateController.add(_devices[index]);
    } else if (message['type'] == 'device_connected') {
      final newDevice = Device(
        id: deviceId,
        name: message['name'] ?? 'Unknown Device',
        type: message['type'] ?? 'unknown',
        platform: message['platform'] ?? 'unknown',
        status: 'online',
        ip: '',
        tailscaleIp: '',
        capabilities: [],
        lastSeen: DateTime.now(),
        battery: 100,
        signal: 'strong',
      );
      _devices.add(newDevice);
    }

    _devicesController.add(List.from(_devices));
  }

  void _handleDeviceDisconnected(Map<String, dynamic> message) {
    final deviceId = message['device_id'];
    final index = _devices.indexWhere((d) => d.id == deviceId);

    if (index >= 0) {
      _devices[index] = _devices[index].copyWith(status: 'offline');
      _devicesController.add(List.from(_devices));
    }
  }

  Future<List<Device>> fetchDevices() async {
    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/v1/devices'), headers: _headers);
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        _devices = data.map((json) => Device.fromJson(json)).toList();
        _devicesController.add(List.from(_devices));
        return _devices;
      }
    } catch (e) {
      print('Failed to fetch devices: $e');
    }
    return [];
  }

  Future<Device?> addDevice({
    required String name,
    required String type,
    required String platform,
    String ip = '',
    String tailscaleIp = '',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/api/v1/devices'),
        headers: _headers,
        body: json.encode({
          'name': name,
          'type': type,
          'platform': platform,
          'ip': ip,
          'tailscale_ip': tailscaleIp,
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        await fetchDevices();
        if (_devices.isEmpty) return null;
        return _devices.firstWhere(
          (d) => d.id == data['device_id'],
          orElse: () => _devices.last,
        );
      }
    } catch (e) {
      print('Failed to add device: $e');
    }
    return null;
  }

  Future<bool> removeDevice(String deviceId) async {
    try {
      final response = await http.delete(
        Uri.parse('$_baseUrl/api/v1/devices/$deviceId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        _devices.removeWhere((d) => d.id == deviceId);
        _devicesController.add(List.from(_devices));
        return true;
      }
    } catch (e) {
      print('Failed to remove device: $e');
    }
    return false;
  }

  void registerDevice(String deviceId, String name, String platform, String type) {
    _webSocketService.send({
      'type': 'device_register',
      'device_id': deviceId,
      'name': name,
      'platform': platform,
      'type': type,
    });
  }

  void sendHeartbeat(String deviceId, {int? battery, String? signal}) {
    _webSocketService.send({
      'type': 'device_heartbeat',
      'device_id': deviceId,
      'battery': battery,
      'signal': signal,
      'status': 'online',
    });
  }

  List<Device> get currentDevices => List.from(_devices);

  void dispose() {
    _devicesController.close();
    _deviceUpdateController.close();
    _deviceEventController.close();
  }
}
