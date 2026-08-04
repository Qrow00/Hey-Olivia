import 'dart:async';
import 'package:flutter/services.dart';
import 'websocket_service.dart';

class HealthBridgeService {
  static const MethodChannel _channel = MethodChannel('health_bridge');

  final WebSocketService _ws;
  final String _deviceId;
  Timer? _pollTimer;
  bool _observing = false;

  HealthBridgeService(this._ws, this._deviceId);

  Future<bool> isAvailable() async {
    try {
      return await _channel.invokeMethod('isAvailable') as bool;
    } catch (_) {
      return false;
    }
  }

  Future<bool> requestPermissions() async {
    try {
      await _channel.invokeMethod('requestPermissions');
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>> readMetrics({int hours = 24}) async {
    try {
      final result = await _channel.invokeMethod('readMetrics', {'hours': hours});
      return Map<String, dynamic>.from(result as Map);
    } catch (_) {
      return {};
    }
  }

  void startObserving({Duration interval = const Duration(seconds: 30)}) {
    if (_observing) return;
    _observing = true;
    _pollTimer = Timer.periodic(interval, (_) => _pollAndRelay());
    _pollAndRelay();
  }

  void stopObserving() {
    _observing = false;
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  Future<void> _pollAndRelay() async {
    final metrics = await readMetrics(hours: 1);
    if (metrics.isEmpty) return;

    for (final entry in metrics.entries) {
      if (entry.key == 'period_hours') continue;
      _ws.send({
        'type': 'wearable_health_update',
        'device_id': _deviceId,
        'metric': entry.key,
        'value': entry.value,
        'unit': _unitFor(entry.key),
      });
    }
  }

  String _unitFor(String metric) {
    switch (metric) {
      case 'heart_rate': return 'bpm';
      case 'steps': return 'count';
      case 'spo2': return '%';
      case 'sleep_hours': return 'hours';
      case 'calories': return 'kcal';
      default: return '';
    }
  }

  void dispose() {
    stopObserving();
  }
}
