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
  final DateTime? lastHeartbeat;
  final int battery;
  final String signal;
  final String osVersion;
  final String appVersion;
  final Map<String, dynamic> metadata;

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
    this.lastHeartbeat,
    required this.battery,
    required this.signal,
    this.osVersion = '',
    this.appVersion = '',
    this.metadata = const {},
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id'],
      name: json['name'],
      type: json['type'],
      platform: json['platform'],
      status: json['status'],
      ip: json['ip'] ?? '',
      tailscaleIp: json['tailscale_ip'] ?? '',
      capabilities: List<String>.from(json['capabilities'] ?? []),
      lastSeen: DateTime.parse(json['last_seen']),
      lastHeartbeat: json['last_heartbeat'] != null
          ? DateTime.parse(json['last_heartbeat'])
          : null,
      battery: json['battery'] ?? 100,
      signal: json['signal'] ?? 'strong',
      osVersion: json['os_version'] ?? '',
      appVersion: json['app_version'] ?? '',
      metadata: Map<String, dynamic>.from(json['metadata'] ?? {}),
    );
  }

  bool get isOnline => status == 'online';
  bool hasCapability(String cap) => capabilities.contains(cap);

  String get lastSeenFormatted {
    final diff = DateTime.now().difference(lastSeen);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }

  Device copyWith({
    String? status,
    int? battery,
    String? signal,
    Map<String, dynamic>? metadata,
  }) {
    return Device(
      id: id,
      name: name,
      type: type,
      platform: platform,
      status: status ?? this.status,
      ip: ip,
      tailscaleIp: tailscaleIp,
      capabilities: capabilities,
      lastSeen: DateTime.now(),
      lastHeartbeat: DateTime.now(),
      battery: battery ?? this.battery,
      signal: signal ?? this.signal,
      osVersion: osVersion,
      appVersion: appVersion,
      metadata: metadata ?? this.metadata,
    );
  }
}
