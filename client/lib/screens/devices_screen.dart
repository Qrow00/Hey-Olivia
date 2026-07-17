import 'package:flutter/material.dart';
import '../widgets/device_card.dart';
import '../models/device.dart';

class DevicesScreen extends StatelessWidget {
  final List<Device> devices;

  const DevicesScreen({super.key, required this.devices});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        title: Text('Devices'),
        backgroundColor: Color(0xFF1a1a2e),
      ),
      body: devices.isEmpty
          ? Center(
              child: Text(
                'No devices connected',
                style: TextStyle(color: Colors.white54),
              ),
            )
          : ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: devices.length,
              itemBuilder: (context, index) {
                return Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: DeviceCard(device: devices[index]),
                );
              },
            ),
    );
  }
}
