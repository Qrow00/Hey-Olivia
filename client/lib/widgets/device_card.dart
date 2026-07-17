import 'package:flutter/material.dart';
import '../models/device.dart';

class DeviceCard extends StatelessWidget {
  final Device device;

  const DeviceCard({super.key, required this.device});

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

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Color(0xFF1a1a2e),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_typeIcon, color: Colors.cyan, size: 32),
                SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        device.name,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        device.platform.toUpperCase(),
                        style: TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _statusColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    device.status,
                    style: TextStyle(color: _statusColor, fontSize: 12),
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStat(Icons.battery_std, '${device.battery}%'),
                _buildStat(Icons.signal_cellular_alt, device.signal),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStat(IconData icon, String value) {
    return Row(
      children: [
        Icon(icon, color: Colors.grey, size: 16),
        SizedBox(width: 4),
        Text(value, style: TextStyle(color: Colors.grey)),
      ],
    );
  }
}
