import 'package:flutter/material.dart';
import '../models/device.dart';

class DeviceCard extends StatelessWidget {
  final Device device;
  final VoidCallback? onTap;
  final VoidCallback? onRemove;

  const DeviceCard({
    super.key,
    required this.device,
    this.onTap,
    this.onRemove,
  });

  Color get _statusColor {
    switch (device.status) {
      case 'online':
        return Colors.green;
      case 'sleeping':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  IconData get _typeIcon {
    switch (device.type) {
      case 'phone':
        return Icons.phone;
      case 'pc':
      case 'laptop':
        return Icons.computer;
      case 'cctv':
        return Icons.camera_alt;
      case 'smart-home':
        return Icons.home;
      default:
        return Icons.device_unknown;
    }
  }

  IconData get _platformIcon {
    switch (device.platform) {
      case 'android':
        return Icons.android;
      case 'ios':
        return Icons.apple;
      case 'windows':
        return Icons.window;
      case 'linux':
        return Icons.terminal;
      default:
        return Icons.device_hub;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        color: Color(0xFF1a1a2e),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(),
              SizedBox(height: 12),
              _buildStats(),
              SizedBox(height: 12),
              _buildCapabilities(),
              if (onRemove != null) _buildActions(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        Container(
          padding: EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: _statusColor.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(_typeIcon, color: _statusColor, size: 28),
        ),
        SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    device.name,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(width: 8),
                  Icon(_platformIcon, color: Colors.grey, size: 16),
                ],
              ),
              SizedBox(height: 2),
              Text(
                '${device.type.toUpperCase()} - ${device.platform.toUpperCase()}',
                style: TextStyle(color: Colors.grey, fontSize: 12),
              ),
            ],
          ),
        ),
        _buildStatusBadge(),
      ],
    );
  }

  Widget _buildStatusBadge() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: _statusColor.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _statusColor.withValues(alpha: 0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _statusColor,
            ),
          ),
          SizedBox(width: 6),
          Text(
            device.status.toUpperCase(),
            style: TextStyle(
              color: _statusColor,
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStats() {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(
            Icons.battery_std,
            '${device.battery}%',
            _batteryColor,
          ),
          _buildStatItem(
            Icons.signal_cellular_alt,
            device.signal.toUpperCase(),
            _signalColor,
          ),
          _buildStatItem(
            Icons.access_time,
            device.lastSeenFormatted,
            Colors.grey,
          ),
        ],
      ),
    );
  }

  Color get _batteryColor {
    if (device.battery > 60) return Colors.green;
    if (device.battery > 20) return Colors.orange;
    return Colors.red;
  }

  Color get _signalColor {
    switch (device.signal) {
      case 'strong':
        return Colors.green;
      case 'medium':
        return Colors.orange;
      default:
        return Colors.red;
    }
  }

  Widget _buildStatItem(IconData icon, String value, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildCapabilities() {
    if (device.capabilities.isEmpty) return SizedBox.shrink();

    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: device.capabilities.map((cap) {
        return Container(
          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.cyan.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.cyan.withValues(alpha: 0.3)),
          ),
          child: Text(
            _capabilityLabel(cap),
            style: TextStyle(
              color: Colors.cyan,
              fontSize: 10,
              fontWeight: FontWeight.w500,
            ),
          ),
        );
      }).toList(),
    );
  }

  String _capabilityLabel(String cap) {
    switch (cap) {
      case 'screen-share':
        return 'SCREEN SHARE';
      case 'voice':
        return 'VOICE';
      case 'camera':
        return 'CAMERA';
      case 'adb':
        return 'ADB';
      case 'ssh':
        return 'SSH';
      case 'rdp':
        return 'RDP';
      case 'rtsp':
        return 'RTSP';
      default:
        return cap.toUpperCase();
    }
  }

  Widget _buildActions() {
    return Padding(
      padding: EdgeInsets.only(top: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          TextButton.icon(
            onPressed: onRemove,
            icon: Icon(Icons.delete_outline, color: Colors.red, size: 18),
            label: Text('Remove', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}
