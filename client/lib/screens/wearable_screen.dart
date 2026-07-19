import 'dart:async';
import 'package:flutter/material.dart';
import '../models/wearable.dart';
import '../services/wearable_service.dart';

class WearableScreen extends StatefulWidget {
  final WearableService wearableService;

  const WearableScreen({super.key, required this.wearableService});

  @override
  State<WearableScreen> createState() => _WearableScreenState();
}

class _WearableScreenState extends State<WearableScreen> {
  StreamSubscription? _deviceSubscription;
  StreamSubscription? _healthSubscription;
  WearableDevice? _selectedDevice;

  @override
  void initState() {
    super.initState();
    _loadDevices();
    _setupListeners();
  }

  void _loadDevices() async {
    await widget.wearableService.fetchDevices();
    if (widget.wearableService.allDevices.isNotEmpty) {
      setState(() {
        _selectedDevice = widget.wearableService.allDevices.first;
      });
    }
  }

  void _setupListeners() {
    _deviceSubscription = widget.wearableService.devices.listen((device) {
      if (mounted) {
        setState(() {
          if (_selectedDevice?.id == device.id) {
            _selectedDevice = device;
          }
        });
      }
    });

    _healthSubscription = widget.wearableService.healthUpdates.listen((data) {
      if (mounted) {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _deviceSubscription?.cancel();
    _healthSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('Health Monitor', style: TextStyle(color: Colors.cyan)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: Colors.cyan),
            onPressed: _loadDevices,
          ),
        ],
      ),
      body: _selectedDevice == null
          ? _buildNoDevice()
          : _buildHealthDashboard(),
    );
  }

  Widget _buildNoDevice() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.watch, size: 64, color: Colors.white24),
          SizedBox(height: 16),
          Text('No wearable connected', style: TextStyle(color: Colors.white70, fontSize: 18)),
          SizedBox(height: 8),
          Text('Connect a smartwatch to monitor health', style: TextStyle(color: Colors.white38)),
          SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => _showAddDeviceDialog(),
            icon: Icon(Icons.add),
            label: Text('Add Device'),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.cyan),
          ),
        ],
      ),
    );
  }

  Widget _buildHealthDashboard() {
    final health = _selectedDevice!.healthSummary;
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildDeviceHeader(),
          SizedBox(height: 20),
          _buildVitalRow(
            icon: Icons.favorite,
            label: 'Heart Rate',
            value: health?.heartRate?.current?.toInt(),
            unit: 'bpm',
            color: Colors.red,
            avg: health?.heartRate?.avg?.toInt(),
          ),
          _buildVitalRow(
            icon: Icons.air,
            label: 'Blood Oxygen',
            value: health?.spo2?.current?.toInt(),
            unit: '%',
            color: Colors.blue,
            avg: health?.spo2?.avg?.toInt(),
          ),
          _buildVitalRow(
            icon: Icons.directions_walk,
            label: 'Steps',
            value: health?.steps?.todayTotal?.toInt(),
            unit: 'today',
            color: Colors.green,
          ),
          _buildVitalRow(
            icon: Icons.bedtime,
            label: 'Sleep',
            value: health?.sleep?.current?.toInt(),
            unit: 'hrs',
            color: Colors.purple,
          ),
          _buildVitalRow(
            icon: Icons.local_fire_department,
            label: 'Calories',
            value: health?.calories?.todayTotal?.toInt(),
            unit: 'kcal',
            color: Colors.orange,
          ),
          _buildVitalRow(
            icon: Icons.psychology,
            label: 'Stress',
            value: health?.stress?.current?.toInt(),
            unit: '',
            color: Colors.teal,
          ),
          _buildVitalRow(
            icon: Icons.thermostat,
            label: 'Temperature',
            value: health?.bodyTemperature?.current?.toInt(),
            unit: '°F',
            color: Colors.amber,
          ),
          SizedBox(height: 20),
          _buildAlertsSection(),
        ],
      ),
    );
  }

  Widget _buildDeviceHeader() {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: Colors.cyan.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.watch, color: Colors.cyan, size: 28),
          ),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_selectedDevice!.name, style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                Text(_selectedDevice!.type.toUpperCase(), style: TextStyle(color: Colors.white54, fontSize: 12)),
              ],
            ),
          ),
          _buildStatusChip(_selectedDevice!.isOnline ? 'Online' : 'Offline', _selectedDevice!.isOnline),
          SizedBox(width: 8),
          _buildBatteryIndicator(_selectedDevice!.battery),
        ],
      ),
    );
  }

  Widget _buildStatusChip(String label, bool isOnline) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isOnline ? Colors.green.withValues(alpha: 0.2) : Colors.red.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isOnline ? Colors.green : Colors.red,
            ),
          ),
          SizedBox(width: 4),
          Text(label, style: TextStyle(color: isOnline ? Colors.green : Colors.red, fontSize: 10)),
        ],
      ),
    );
  }

  Widget _buildBatteryIndicator(int level) {
    Color color;
    if (level > 50) color = Colors.green;
    else if (level > 20) color = Colors.yellow;
    else color = Colors.red;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.battery_std, color: color, size: 20),
        SizedBox(width: 2),
        Text('$level%', style: TextStyle(color: color, fontSize: 10)),
      ],
    );
  }

  Widget _buildVitalRow({
    required IconData icon,
    required String label,
    required int? value,
    required String unit,
    required Color color,
    int? avg,
  }) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: Colors.white54, fontSize: 12)),
                SizedBox(height: 4),
                value != null
                    ? Text(
                        '$value',
                        style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold),
                      )
                    : Text('--', style: TextStyle(color: Colors.white24, fontSize: 28)),
              ],
            ),
          ),
          if (value != null && unit.isNotEmpty)
            Text(unit, style: TextStyle(color: Colors.white38, fontSize: 14)),
          if (avg != null) ...[
            SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('AVG', style: TextStyle(color: Colors.white38, fontSize: 10)),
                Text('$avg', style: TextStyle(color: Colors.white54, fontSize: 14)),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAlertsSection() {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber, color: Colors.amber, size: 20),
              SizedBox(width: 8),
              Text('Health Alerts', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
            ],
          ),
          SizedBox(height: 12),
          Text(
            'No alerts - all vitals normal',
            style: TextStyle(color: Colors.white38, fontSize: 13),
          ),
        ],
      ),
    );
  }

  void _showAddDeviceDialog() {
    final nameController = TextEditingController();
    String selectedType = 'smartwatch';

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: Color(0xFF1a1a2e),
          title: Text('Add Wearable', style: TextStyle(color: Colors.cyan)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Device Name',
                  labelStyle: TextStyle(color: Colors.white54),
                  hintText: 'e.g., My Galaxy Watch',
                  hintStyle: TextStyle(color: Colors.white24),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                ),
              ),
              SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedType,
                dropdownColor: Color(0xFF1a1a2e),
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Device Type',
                  labelStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                ),
                items: [
                  DropdownMenuItem(value: 'smartwatch', child: Text('Smartwatch')),
                  DropdownMenuItem(value: 'fitness_band', child: Text('Fitness Band')),
                  DropdownMenuItem(value: 'smart_ring', child: Text('Smart Ring')),
                  DropdownMenuItem(value: 'medical_device', child: Text('Medical Device')),
                ],
                onChanged: (value) {
                  setDialogState(() => selectedType = value!);
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Cancel', style: TextStyle(color: Colors.white70)),
            ),
            TextButton(
              onPressed: () async {
                if (nameController.text.isNotEmpty) {
                  await widget.wearableService.registerDevice(
                    name: nameController.text,
                    type: selectedType,
                  );
                  Navigator.pop(context);
                  _loadDevices();
                }
              },
              child: Text('Add', style: TextStyle(color: Colors.cyan)),
            ),
          ],
        ),
      ),
    );
  }
}
