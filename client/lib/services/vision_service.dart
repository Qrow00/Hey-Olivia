import 'dart:async';
import 'websocket_service.dart';

class VisionResult {
  final String cameraId;
  final String cameraName;
  final String description;
  final int peopleCount;
  final List<String> peopleActions;
  final List<String> objectsDetected;
  final bool motionDetected;
  final List<String> alerts;
  final String model;
  final String status;

  VisionResult({
    required this.cameraId,
    required this.cameraName,
    required this.description,
    this.peopleCount = 0,
    this.peopleActions = const [],
    this.objectsDetected = const [],
    this.motionDetected = false,
    this.alerts = const [],
    this.model = '',
    this.status = 'success',
  });

  factory VisionResult.fromJson(Map<String, dynamic> json) {
    return VisionResult(
      cameraId: json['camera_id'] ?? '',
      cameraName: json['camera_name'] ?? '',
      description: json['description'] ?? '',
      peopleCount: json['people_count'] ?? 0,
      peopleActions: List<String>.from(json['people_actions'] ?? []),
      objectsDetected: List<String>.from(json['objects_detected'] ?? []),
      motionDetected: json['motion_detected'] ?? false,
      alerts: List<String>.from(json['alerts'] ?? []),
      model: json['model'] ?? '',
      status: json['status'] ?? 'success',
    );
  }
}

class VisionObservation {
  final String camera;
  final String description;
  final int peopleCount;
  final List<String> peopleActions;
  final bool motion;
  final double timestamp;

  VisionObservation({
    required this.camera,
    required this.description,
    this.peopleCount = 0,
    this.peopleActions = const [],
    this.motion = false,
    required this.timestamp,
  });

  factory VisionObservation.fromJson(Map<String, dynamic> json) {
    return VisionObservation(
      camera: json['camera'] ?? '',
      description: json['description'] ?? '',
      peopleCount: json['people_count'] ?? 0,
      peopleActions: List<String>.from(json['people_actions'] ?? []),
      motion: json['motion'] ?? false,
      timestamp: (json['timestamp'] ?? 0).toDouble(),
    );
  }
}

class VisionService {
  final WebSocketService _webSocketService;
  final String baseUrl;

  final StreamController<VisionResult> _resultController =
      StreamController<VisionResult>.broadcast();
  final StreamController<VisionObservation> _observationController =
      StreamController<VisionObservation>.broadcast();
  final StreamController<Map<String, dynamic>> _alertController =
      StreamController<Map<String, dynamic>>.broadcast();

  Stream<VisionResult> get results => _resultController.stream;
  Stream<VisionObservation> get observations => _observationController.stream;
  Stream<Map<String, dynamic>> get alerts => _alertController.stream;

  String? _activeObservationSession;
  String? get activeSession => _activeObservationSession;

  VisionService(this._webSocketService, {this.baseUrl = 'http://localhost:8000'}) {
    _setupWebSocketListeners();
  }

  void _setupWebSocketListeners() {
    _webSocketService.messages.listen((message) {
      final type = message['type'];

      if (type == 'vision_result') {
        final result = VisionResult.fromJson(message['result'] ?? {});
        _resultController.add(result);
      } else if (type == 'vision_scan_result') {
        final results = (message['results'] as List?)
            ?.map((r) => VisionResult.fromJson(r))
            .toList() ?? [];
        for (var result in results) {
          _resultController.add(result);
        }
      } else if (type == 'vision_observation') {
        _observationController.add(VisionObservation.fromJson(message));
      } else if (type == 'vision_alert') {
        _alertController.add(message);
      } else if (type == 'vision_observe_started') {
        _activeObservationSession = message['session_id'];
      } else if (type == 'vision_observe_stopped') {
        _activeObservationSession = null;
      }
    });
  }

  void analyzeCamera(String cameraId, {String? prompt, String? context}) {
    _webSocketService.send({
      'type': 'vision_analyze',
      'camera_id': cameraId,
      'prompt': prompt,
      'context': context,
    });
  }

  void quickLook(String cameraId) {
    _webSocketService.send({
      'type': 'vision_quick_look',
      'camera_id': cameraId,
    });
  }

  void scanAllCameras() {
    _webSocketService.send({
      'type': 'vision_scan_all',
    });
  }

  void startObservation({
    required String sessionId,
    required List<String> cameraIds,
    String mode = 'watch',
    double interval = 10.0,
    bool alertOnMotion = true,
    bool alertOnPerson = true,
    bool trackPeople = true,
    String? customPrompt,
  }) {
    _webSocketService.send({
      'type': 'vision_observe_start',
      'session_id': sessionId,
      'camera_ids': cameraIds,
      'mode': mode,
      'interval': interval,
      'alert_on_motion': alertOnMotion,
      'alert_on_person': alertOnPerson,
      'track_people': trackPeople,
      'custom_prompt': customPrompt,
    });
    _activeObservationSession = sessionId;
  }

  void stopObservation() {
    if (_activeObservationSession != null) {
      _webSocketService.send({
        'type': 'vision_observe_stop',
        'session_id': _activeObservationSession,
      });
      _activeObservationSession = null;
    }
  }

  void askAboutCamera(String cameraId, String question) {
    _webSocketService.send({
      'type': 'vision_analyze',
      'camera_id': cameraId,
      'prompt': 'A user is asking about this camera feed: "$question"\nAnalyze the camera and answer their question based on what you see. Be specific and helpful.',
    });
  }

  void dispose() {
    _resultController.close();
    _observationController.close();
    _alertController.close();
  }
}
