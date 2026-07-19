class SmartDevice {
  final String id;
  final String name;
  final String type;
  final String protocol;
  final String ip;
  final String topic;
  final String room;
  final bool isOnline;
  final bool isOn;
  final int brightness;
  final String color;
  final double temperature;
  final double humidity;
  final int battery;
  final Map<String, dynamic> state;
  final List<String> capabilities;
  final double lastUpdate;

  SmartDevice({
    required this.id,
    required this.name,
    required this.type,
    required this.protocol,
    this.ip = '',
    this.topic = '',
    this.room = '',
    this.isOnline = false,
    this.isOn = false,
    this.brightness = 100,
    this.color = '#ffffff',
    this.temperature = 22.0,
    this.humidity = 0,
    this.battery = 100,
    this.state = const {},
    this.capabilities = const [],
    this.lastUpdate = 0,
  });

  factory SmartDevice.fromJson(Map<String, dynamic> json) {
    return SmartDevice(
      id: json['id'],
      name: json['name'],
      type: json['type'] ?? 'light',
      protocol: json['protocol'] ?? 'mqtt',
      ip: json['ip'] ?? '',
      topic: json['topic'] ?? '',
      room: json['room'] ?? '',
      isOnline: json['is_online'] ?? false,
      isOn: json['is_on'] ?? false,
      brightness: json['brightness'] ?? 100,
      color: json['color'] ?? '#ffffff',
      temperature: (json['temperature'] ?? 22.0).toDouble(),
      humidity: (json['humidity'] ?? 0).toDouble(),
      battery: json['battery'] ?? 100,
      state: json['state'] ?? {},
      capabilities: List<String>.from(json['capabilities'] ?? []),
      lastUpdate: (json['last_update'] ?? 0).toDouble(),
    );
  }
}
