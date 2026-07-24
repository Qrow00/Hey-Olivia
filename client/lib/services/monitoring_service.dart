import 'dart:async';
import 'dart:convert';
import 'websocket_service.dart';

class MonitoringData {
  final double cpuPercent;
  final double ramPercent;
  final double ramUsedGb;
  final double ramTotalGb;
  final double diskPercent;
  final double diskUsedGb;
  final double diskTotalGb;
  final double? gpuLoad;
  final double? gpuTemp;
  final double? gpuMemoryPercent;
  final String? gpuName;
  final double? cpuFreq;
  final int? cpuCount;
  final double netSentGb;
  final double netRecvGb;
  final double uptimeHours;
  final bool alert;
  final List<Map<String, dynamic>> alertDetails;
  final String timestampIso;

  MonitoringData({
    required this.cpuPercent,
    required this.ramPercent,
    required this.ramUsedGb,
    required this.ramTotalGb,
    required this.diskPercent,
    required this.diskUsedGb,
    required this.diskTotalGb,
    this.gpuLoad,
    this.gpuTemp,
    this.gpuMemoryPercent,
    this.gpuName,
    this.cpuFreq,
    this.cpuCount,
    required this.netSentGb,
    required this.netRecvGb,
    required this.uptimeHours,
    required this.alert,
    required this.alertDetails,
    required this.timestampIso,
  });

  factory MonitoringData.fromJson(Map<String, dynamic> json) {
    return MonitoringData(
      cpuPercent: (json['cpu_percent'] ?? 0).toDouble(),
      ramPercent: (json['ram_percent'] ?? 0).toDouble(),
      ramUsedGb: (json['ram_used_gb'] ?? 0).toDouble(),
      ramTotalGb: (json['ram_total_gb'] ?? 0).toDouble(),
      diskPercent: (json['disk_percent'] ?? 0).toDouble(),
      diskUsedGb: (json['disk_used_gb'] ?? 0).toDouble(),
      diskTotalGb: (json['disk_total_gb'] ?? 0).toDouble(),
      gpuLoad: json['gpu_load']?.toDouble(),
      gpuTemp: json['gpu_temp']?.toDouble(),
      gpuMemoryPercent: json['gpu_memory_percent']?.toDouble(),
      gpuName: json['gpu_name'],
      cpuFreq: json['cpu_freq']?.toDouble(),
      cpuCount: json['cpu_count'],
      netSentGb: (json['net_sent_gb'] ?? 0).toDouble(),
      netRecvGb: (json['net_recv_gb'] ?? 0).toDouble(),
      uptimeHours: (json['uptime_hours'] ?? 0).toDouble(),
      alert: json['alert'] ?? false,
      alertDetails: (json['alert_details'] as List?)
              ?.map((e) => Map<String, dynamic>.from(e))
              .toList() ??
          [],
      timestampIso: json['timestamp_iso'] ?? '',
    );
  }
}

class AlertData {
  final String ruleId;
  final String metric;
  final String severity;
  final String message;
  final double value;
  final double threshold;
  final String timestamp;

  AlertData({
    required this.ruleId,
    required this.metric,
    required this.severity,
    required this.message,
    required this.value,
    required this.threshold,
    required this.timestamp,
  });

  factory AlertData.fromJson(Map<String, dynamic> json) {
    return AlertData(
      ruleId: json['rule_id'] ?? '',
      metric: json['metric'] ?? '',
      severity: json['severity'] ?? 'warning',
      message: json['message'] ?? '',
      value: (json['value'] ?? 0).toDouble(),
      threshold: (json['threshold'] ?? 0).toDouble(),
      timestamp: json['timestamp'] ?? '',
    );
  }
}

class ProcessData {
  final String name;
  final int pid;
  final double cpuSeconds;
  final double memoryMb;

  ProcessData({
    required this.name,
    required this.pid,
    required this.cpuSeconds,
    required this.memoryMb,
  });

  factory ProcessData.fromJson(Map<String, dynamic> json) {
    return ProcessData(
      name: json['name'] ?? '',
      pid: json['pid'] ?? 0,
      cpuSeconds: (json['cpu_seconds'] ?? 0).toDouble(),
      memoryMb: (json['memory_mb'] ?? 0).toDouble(),
    );
  }
}

class ActivityEntry {
  final String category;
  final String detail;
  final String timestampIso;

  ActivityEntry({
    required this.category,
    required this.detail,
    required this.timestampIso,
  });

  factory ActivityEntry.fromJson(Map<String, dynamic> json) {
    return ActivityEntry(
      category: json['category'] ?? '',
      detail: json['detail'] ?? '',
      timestampIso: json['timestamp_iso'] ?? '',
    );
  }
}

class MonitoringService {
  final WebSocketService _webSocket;
  MonitoringData? _latest;
  List<AlertData> _alerts = [];
  List<ProcessData> _processes = [];
  List<ActivityEntry> _activityLog = [];
  Timer? _pollTimer;

  final _snapshotController = StreamController<MonitoringData>.broadcast();
  final _alertController = StreamController<List<AlertData>>.broadcast();
  final _processController = StreamController<List<ProcessData>>.broadcast();
  final _activityController = StreamController<List<ActivityEntry>>.broadcast();

  Stream<MonitoringData> get snapshot => _snapshotController.stream;
  Stream<List<AlertData>> get alerts => _alertController.stream;
  Stream<List<ProcessData>> get processes => _processController.stream;
  Stream<List<ActivityEntry>> get activityLog => _activityController.stream;
  MonitoringData? get latest => _latest;
  List<AlertData> get currentAlerts => _alerts;
  List<ProcessData> get currentProcesses => _processes;
  List<ActivityEntry> get currentActivity => _activityLog;

  MonitoringService(this._webSocket) {
    _setupListeners();
  }

  void _setupListeners() {
    _webSocket.messages.listen((message) {
      final type = message['type'];

      if (type == 'monitoring_snapshot') {
        final data = message['data'];
        if (data != null) {
          _latest = MonitoringData.fromJson(Map<String, dynamic>.from(data));
          _snapshotController.add(_latest!);
        }
      } else if (type == 'system_alert') {
        final alert = message['alert'];
        if (alert != null) {
          _alerts.add(AlertData.fromJson(Map<String, dynamic>.from(alert)));
          if (_alerts.length > 50) _alerts = _alerts.sublist(_alerts.length - 50);
          _alertController.add(List.unmodifiable(_alerts));
        }
      } else if (type == 'monitoring_alerts') {
        final list = message['alerts'] as List?;
        if (list != null) {
          _alerts = list
              .map((e) => AlertData.fromJson(Map<String, dynamic>.from(e)))
              .toList();
          _alertController.add(List.unmodifiable(_alerts));
        }
      } else if (type == 'activity_processes') {
        final list = message['processes'] as List?;
        if (list != null) {
          _processes = list
              .map((e) => ProcessData.fromJson(Map<String, dynamic>.from(e)))
              .toList();
          _processController.add(List.unmodifiable(_processes));
        }
      } else if (type == 'activity_log') {
        final list = message['activity'] as List?;
        if (list != null) {
          _activityLog = list
              .map((e) => ActivityEntry.fromJson(Map<String, dynamic>.from(e)))
              .toList();
          _activityController.add(List.unmodifiable(_activityLog));
        }
      }
    });
  }

  void requestSnapshot() {
    _webSocket.send({'type': 'monitoring_snapshot'});
  }

  void requestAlerts({int limit = 20}) {
    _webSocket.send({'type': 'monitoring_alerts', 'limit': limit});
  }

  void requestProcesses() {
    _webSocket.send({'type': 'activity_processes'});
  }

  void requestActivityLog({int limit = 20}) {
    _webSocket.send({'type': 'activity_log', 'limit': limit});
  }

  void setThreshold(String metric, double value) {
    _webSocket.send({
      'type': 'monitoring_set_threshold',
      'metric': metric,
      'value': value,
    });
  }

  void startAutoRefresh({Duration interval = const Duration(seconds: 30)}) {
    _pollTimer?.cancel();
    requestSnapshot();
    _pollTimer = Timer.periodic(interval, (_) {
      requestSnapshot();
    });
  }

  void stopAutoRefresh() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  void dispose() {
    _pollTimer?.cancel();
    _snapshotController.close();
    _alertController.close();
    _processController.close();
    _activityController.close();
  }
}
