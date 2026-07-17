class Device {
  final String id;
  final String name;
  final String type;
  final String platform;
  final String status;
  final String ip;
  final String tailscaleIp;
  final List<String> capabilities;
  final DateTime lastSeen;
  final int battery;
  final String signal;

  Device({
    required this.id,
    required this.name,
    required this.type,
    required this.platform,
    required this.status,
    required this.ip,
    required this.tailscaleIp,
    required this.capabilities,
    required this.lastSeen,
    required this.battery,
    required this.signal,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id'],
      name: json['name'],
      type: json['type'],
      platform: json['platform'],
      status: json['status'],
      ip: json['ip'],
      tailscaleIp: json['tailscale_ip'],
      capabilities: List<String>.from(json['capabilities']),
      lastSeen: DateTime.parse(json['last_seen']),
      battery: json['battery'] ?? 100,
      signal: json['signal'] ?? 'strong',
    );
  }
}
