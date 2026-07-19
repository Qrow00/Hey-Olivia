class WearableDevice {
  final String id;
  final String name;
  final String type;
  final String platform;
  final bool isOnline;
  final int battery;
  final String firmwareVersion;
  final double lastSync;
  final HealthSummary? healthSummary;

  WearableDevice({
    required this.id,
    required this.name,
    required this.type,
    required this.platform,
    this.isOnline = false,
    this.battery = 100,
    this.firmwareVersion = '',
    this.lastSync = 0,
    this.healthSummary,
  });

  factory WearableDevice.fromJson(Map<String, dynamic> json) {
    return WearableDevice(
      id: json['id'],
      name: json['name'],
      type: json['type'] ?? 'smartwatch',
      platform: json['platform'] ?? 'unknown',
      isOnline: json['is_online'] ?? false,
      battery: json['battery'] ?? 100,
      firmwareVersion: json['firmware_version'] ?? '',
      lastSync: (json['last_sync'] ?? 0).toDouble(),
      healthSummary: json['health_summary'] != null
          ? HealthSummary.fromJson(json['health_summary'])
          : null,
    );
  }
}

class HealthSummary {
  final HealthMetricData? heartRate;
  final HealthMetricData? spo2;
  final HealthMetricData? steps;
  final HealthMetricData? sleep;
  final HealthMetricData? calories;
  final HealthMetricData? stress;
  final HealthMetricData? bloodPressure;
  final HealthMetricData? bodyTemperature;

  HealthSummary({
    this.heartRate,
    this.spo2,
    this.steps,
    this.sleep,
    this.calories,
    this.stress,
    this.bloodPressure,
    this.bodyTemperature,
  });

  factory HealthSummary.fromJson(Map<String, dynamic> json) {
    return HealthSummary(
      heartRate: json['heart_rate'] != null
          ? HealthMetricData.fromJson(json['heart_rate'])
          : null,
      spo2: json['spo2'] != null
          ? HealthMetricData.fromJson(json['spo2'])
          : null,
      steps: json['steps'] != null
          ? HealthMetricData.fromJson(json['steps'])
          : null,
      sleep: json['sleep'] != null
          ? HealthMetricData.fromJson(json['sleep'])
          : null,
      calories: json['calories'] != null
          ? HealthMetricData.fromJson(json['calories'])
          : null,
      stress: json['stress'] != null
          ? HealthMetricData.fromJson(json['stress'])
          : null,
      bloodPressure: json['blood_pressure'] != null
          ? HealthMetricData.fromJson(json['blood_pressure'])
          : null,
      bodyTemperature: json['body_temperature'] != null
          ? HealthMetricData.fromJson(json['body_temperature'])
          : null,
    );
  }
}

class HealthMetricData {
  final double current;
  final String unit;
  final double? avg;
  final double? min;
  final double? max;
  final double? todayTotal;

  HealthMetricData({
    required this.current,
    required this.unit,
    this.avg,
    this.min,
    this.max,
    this.todayTotal,
  });

  factory HealthMetricData.fromJson(Map<String, dynamic> json) {
    return HealthMetricData(
      current: (json['current'] ?? 0).toDouble(),
      unit: json['unit'] ?? '',
      avg: json['avg']?.toDouble(),
      min: json['min']?.toDouble(),
      max: json['max']?.toDouble(),
      todayTotal: json['today_total']?.toDouble(),
    );
  }
}

class HealthAlert {
  final String type;
  final String severity;
  final String message;
  final double value;

  HealthAlert({
    required this.type,
    required this.severity,
    required this.message,
    required this.value,
  });

  factory HealthAlert.fromJson(Map<String, dynamic> json) {
    return HealthAlert(
      type: json['type'],
      severity: json['severity'],
      message: json['message'],
      value: (json['value'] ?? 0).toDouble(),
    );
  }
}
