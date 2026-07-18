import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/services.dart';
import 'websocket_service.dart';

class ScreenShareService {
  final WebSocketService _webSocketService;
  static const MethodChannel _channel = MethodChannel('screen_capture');

  final _sessionController = StreamController<Map<String, dynamic>>.broadcast();
  final _frameController = StreamController<Uint8List>.broadcast();
  final _analysisController = StreamController<Map<String, dynamic>>.broadcast();
  final _viewerCountController = StreamController<int>.broadcast();

  Stream<Map<String, dynamic>> get sessionEvents => _sessionController.stream;
  Stream<Uint8List> get frames => _frameController.stream;
  Stream<Map<String, dynamic>> get analysis => _analysisController.stream;
  Stream<int> get viewerCount => _viewerCountController.stream;

  String? _currentSessionId;
  bool _isStreaming = false;
  Timer? _frameTimer;

  int _fps = 5;
  int _quality = 80;

  ScreenShareService(this._webSocketService) {
    _webSocketService.messages.listen(_handleMessage);
  }

  void _handleMessage(Map<String, dynamic> message) {
    final type = message['type'];

    switch (type) {
      case 'screen_started':
        _currentSessionId = message['session_id'];
        _sessionController.add(message);
        break;
      case 'screen_stopped':
        _currentSessionId = null;
        _isStreaming = false;
        _frameTimer?.cancel();
        _sessionController.add(message);
        break;
      case 'screen_frame':
        final frameB64 = message['frame'];
        if (frameB64 != null) {
          final frameBytes = base64Decode(frameB64);
          _frameController.add(frameBytes);
        }
        break;
      case 'screen_viewing':
        _viewerCountController.add(message['viewer_count'] ?? 0);
        _sessionController.add(message);
        break;
      case 'screen_unviewing':
        _viewerCountController.add(message['viewer_count'] ?? 0);
        break;
      case 'screen_viewer_joined':
        _viewerCountController.add(message['viewer_count'] ?? 0);
        break;
      case 'screen_analysis':
        _analysisController.add(message);
        break;
      case 'screen_session_available':
        _sessionController.add(message);
        break;
      case 'screen_session_ended':
        _sessionController.add(message);
        break;
    }
  }

  Future<void> startStreaming({
    required String deviceId,
    String source = 'pc',
    int fps = 5,
    int quality = 80,
    int width = 720,
    int height = 1280,
  }) async {
    _fps = fps;
    _quality = quality;

    try {
      final started = await _channel.invokeMethod<bool>('startCapture', {
        'width': width,
        'height': height,
        'fps': fps,
      });

      if (started == true) {
        _isStreaming = true;

        _webSocketService.send({
          'type': 'screen_start',
          'device_id': deviceId,
          'source': source,
          'fps': fps,
          'quality': quality,
          'width': width,
          'height': height,
        });

        final interval = Duration(milliseconds: (1000 / fps).round());
        _frameTimer = Timer.periodic(interval, (timer) {
          if (!_isStreaming) {
            timer.cancel();
            return;
          }
          _captureAndSendFrame();
        });
      }
    } catch (e) {
      print('Failed to start capture: $e');
    }
  }

  Future<void> _captureAndSendFrame() async {
    if (!_isStreaming || _currentSessionId == null) return;

    try {
      final frameBytes = await _channel.invokeMethod<Uint8List>('captureFrame');
      if (frameBytes != null && frameBytes.isNotEmpty) {
        _webSocketService.send({
          'type': 'screen_frame',
          'session_id': _currentSessionId,
          'frame': base64Encode(frameBytes),
        });
      }
    } catch (e) {
      print('Frame capture error: $e');
    }
  }

  Future<void> stopStreaming() async {
    _isStreaming = false;
    _frameTimer?.cancel();

    try {
      await _channel.invokeMethod('stopCapture');
    } catch (e) {
      print('Stop capture error: $e');
    }

    if (_currentSessionId != null) {
      _webSocketService.send({
        'type': 'screen_stop',
        'session_id': _currentSessionId,
      });
    }
  }

  void viewSession(String sessionId) {
    _webSocketService.send({
      'type': 'screen_view',
      'session_id': sessionId,
    });
  }

  void unviewSession() {
    if (_currentSessionId != null) {
      _webSocketService.send({
        'type': 'screen_unview',
        'session_id': _currentSessionId,
      });
    }
  }

  void requestAnalysis(String sessionId, {String? frame, String? prompt}) {
    _webSocketService.send({
      'type': 'screen_analyze',
      'session_id': sessionId,
      'frame': frame,
      'prompt': prompt ?? 'Describe what is on this screen',
    });
  }

  Future<bool> isCapturing() async {
    try {
      return await _channel.invokeMethod<bool>('isCapturing') ?? false;
    } catch (e) {
      return false;
    }
  }

  String? get currentSessionId => _currentSessionId;
  bool get isStreaming => _isStreaming;

  void dispose() {
    _frameTimer?.cancel();
    _sessionController.close();
    _frameController.close();
    _analysisController.close();
    _viewerCountController.close();
  }
}
