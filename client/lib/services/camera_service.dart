import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'websocket_service.dart';

class CameraDevice {
  final String id;
  final String name;
  final String url;
  final String type;
  final String location;
  final bool isOnline;
  final bool isStreaming;
  final int viewerCount;
  final int fps;

  CameraDevice({
    required this.id,
    required this.name,
    required this.url,
    this.type = 'cctv',
    this.location = '',
    this.isOnline = false,
    this.isStreaming = false,
    this.viewerCount = 0,
    this.fps = 5,
  });

  factory CameraDevice.fromJson(Map<String, dynamic> json) {
    return CameraDevice(
      id: json['id'],
      name: json['name'],
      url: json['url'],
      type: json['type'] ?? 'cctv',
      location: json['location'] ?? '',
      isOnline: json['is_online'] ?? false,
      isStreaming: json['is_streaming'] ?? false,
      viewerCount: json['viewer_count'] ?? 0,
      fps: json['fps'] ?? 5,
    );
  }
}

class CameraFrame {
  final String cameraId;
  final String frame;
  final String timestamp;

  CameraFrame({
    required this.cameraId,
    required this.frame,
    required this.timestamp,
  });
}

class CameraService {
  final WebSocketService _webSocketService;
  final String baseUrl;
  final StreamController<CameraFrame> _frameController =
      StreamController<CameraFrame>.broadcast();
  final StreamController<CameraDevice> _deviceController =
      StreamController<CameraDevice>.broadcast();

  Stream<CameraFrame> get frames => _frameController.stream;
  Stream<CameraDevice> get deviceUpdates => _deviceController.stream;

  List<CameraDevice> _cameras = [];
  List<CameraDevice> get allCameras => _cameras;
  String? _viewingCameraId;

  CameraService(this._webSocketService, {this.baseUrl = 'http://localhost:8000'}) {
    _setupWebSocketListeners();
  }

  void _setupWebSocketListeners() {
    _webSocketService.messages.listen((message) {
      final type = message['type'];

      if (type == 'camera_frame') {
        if (message['status'] != 'error') {
          _frameController.add(CameraFrame(
            cameraId: message['camera_id'],
            frame: message['frame'],
            timestamp: message['timestamp'],
          ));
        }
      } else if (type == 'camera_viewing') {
        _viewingCameraId = message['camera_id'];
      } else if (type == 'camera_unviewing') {
        _viewingCameraId = null;
      }
    });
  }

  Future<List<CameraDevice>> fetchCameras() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/cameras'));
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        _cameras = data.map((c) => CameraDevice.fromJson(c)).toList();
        return _cameras;
      }
    } catch (e) {
      print('Error fetching cameras: $e');
    }
    return [];
  }

  Future<CameraDevice?> addCamera({
    required String name,
    required String url,
    String username = '',
    String password = '',
    String type = 'cctv',
    String location = '',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/cameras'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'name': name,
          'url': url,
          'username': username,
          'password': password,
          'type': type,
          'location': location,
        }),
      );
      if (response.statusCode == 200) {
        await fetchCameras();
        return _cameras.isNotEmpty ? _cameras.last : null;
      }
    } catch (e) {
      print('Error adding camera: $e');
    }
    return null;
  }

  Future<void> removeCamera(String cameraId) async {
    try {
      await http.delete(Uri.parse('$baseUrl/api/v1/cameras/$cameraId'));
      _cameras.removeWhere((c) => c.id == cameraId);
    } catch (e) {
      print('Error removing camera: $e');
    }
  }

  void startViewing(String cameraId) {
    _webSocketService.send({
      'type': 'camera_view',
      'camera_id': cameraId,
    });
    _viewingCameraId = cameraId;
    _requestFrame(cameraId);
  }

  void stopViewing() {
    if (_viewingCameraId != null) {
      _webSocketService.send({
        'type': 'camera_unview',
        'camera_id': _viewingCameraId,
      });
      _viewingCameraId = null;
    }
  }

  void _requestFrame(String cameraId) {
    _webSocketService.send({
      'type': 'camera_frame_request',
      'camera_id': cameraId,
    });
  }

  void requestNextFrame() {
    if (_viewingCameraId != null) {
      _requestFrame(_viewingCameraId!);
    }
  }

  String? get currentCameraId => _viewingCameraId;

  void dispose() {
    _frameController.close();
    _deviceController.close();
  }
}
