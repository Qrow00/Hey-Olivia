import 'dart:async';
import 'package:flutter/material.dart';
import '../widgets/device_card.dart';
import '../models/device.dart';
import '../services/device_service.dart';
import '../utils/theme.dart';

const _bg = AppTheme.bg;
const _panel = AppTheme.panel;

class DevicesScreen extends StatefulWidget {
  final DeviceService? deviceService;

  const DevicesScreen({super.key, this.deviceService});

  @override
  State<DevicesScreen> createState() => _DevicesScreenState();
}

class _DevicesScreenState extends State<DevicesScreen> {
  List<Device> _devices = [];
  String _filter = 'all';
  StreamSubscription? _devicesSubscription;

  @override
  void initState() {
    super.initState();
    _loadDevices();
  }

  @override
  void didUpdateWidget(DevicesScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.deviceService != oldWidget.deviceService) {
      _devicesSubscription?.cancel();
      _setupStream();
    }
  }

  void _loadDevices() async {
    if (widget.deviceService != null) {
      final devices = await widget.deviceService!.fetchDevices();
      setState(() => _devices = devices);
      _setupStream();
    }
  }

  void _setupStream() {
    _devicesSubscription = widget.deviceService!.devices.listen((devices) {
      setState(() => _devices = devices);
    });
  }

  @override
  void dispose() {
    _devicesSubscription?.cancel();
    super.dispose();
  }

  List<Device> get _filteredDevices {
    if (_filter == 'all') return _devices;
    return _devices.where((d) => d.status == _filter).toList();
  }

  int get _onlineCount => _devices.where((d) => d.status == 'online').length;
  int get _offlineCount => _devices.where((d) => d.status == 'offline').length;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        title: Text('Devices'),
        backgroundColor: _panel,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadDevices,
          ),
          IconButton(
            icon: Icon(Icons.add),
            onPressed: _showAddDeviceDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSummaryBar(),
          _buildFilterBar(),
          Expanded(child: _buildDeviceList()),
        ],
      ),
    );
  }

  Widget _buildSummaryBar() {
    return Container(
      padding: EdgeInsets.all(16),
      color: _panel,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryItem('TOTAL', _devices.length, Colors.cyan),
          _buildSummaryItem('ONLINE', _onlineCount, Colors.green),
          _buildSummaryItem('OFFLINE', _offlineCount, Colors.grey),
        ],
      ),
    );
  }

  Widget _buildSummaryItem(String label, int count, Color color) {
    return Column(
      children: [
        Text(
          count.toString(),
          style: TextStyle(
            color: color,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(color: Colors.white54, fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildFilterBar() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          _buildFilterChip('All', 'all'),
          SizedBox(width: 8),
          _buildFilterChip('Online', 'online'),
          SizedBox(width: 8),
          _buildFilterChip('Offline', 'offline'),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, String value) {
    final isSelected = _filter == value;
    return GestureDetector(
      onTap: () => setState(() => _filter = value),
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected
              ? Colors.cyan.withValues(alpha: 0.3)
              : Colors.white.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? Colors.cyan : Colors.white24,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.cyan : Colors.white70,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  Widget _buildDeviceList() {
    final filtered = _filteredDevices;

    if (filtered.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.devices_other, color: Colors.white24, size: 64),
            SizedBox(height: 16),
            Text(
              _devices.isEmpty ? 'No devices connected' : 'No devices match filter',
              style: TextStyle(color: Colors.white54, fontSize: 16),
            ),
            if (_devices.isEmpty)
              Padding(
                padding: EdgeInsets.only(top: 16),
                child: ElevatedButton.icon(
                  onPressed: _showAddDeviceDialog,
                  icon: Icon(Icons.add),
                  label: Text('Add Device'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.cyan,
                    foregroundColor: Colors.black,
                  ),
                ),
              ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: filtered.length,
      itemBuilder: (context, index) {
        final device = filtered[index];
        return Padding(
          padding: EdgeInsets.only(bottom: 12),
          child: DeviceCard(
            device: device,
            onTap: () => _showDeviceDetails(device),
            onRemove: () => _confirmRemove(device),
          ),
        );
      },
    );
  }

  void _showDeviceDetails(Device device) {
    showModalBottomSheet(
      context: context,
      backgroundColor: _panel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _buildDeviceDetailsSheet(device),
    );
  }

  Widget _buildDeviceDetailsSheet(Device device) {
    return Padding(
      padding: EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.white24,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          SizedBox(height: 20),
          Text(
            device.name,
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            '${device.type.toUpperCase()} - ${device.platform.toUpperCase()}',
            style: TextStyle(color: Colors.cyan),
          ),
          SizedBox(height: 20),
          _buildDetailRow('Status', device.status.toUpperCase()),
          _buildDetailRow('IP Address', device.ip.isNotEmpty ? device.ip : 'N/A'),
          _buildDetailRow('Tailscale IP', device.tailscaleIp.isNotEmpty ? device.tailscaleIp : 'N/A'),
          _buildDetailRow('Battery', '${device.battery}%'),
          _buildDetailRow('Signal', device.signal.toUpperCase()),
          _buildDetailRow('Last Seen', device.lastSeenFormatted),
          if (device.osVersion.isNotEmpty)
            _buildDetailRow('OS Version', device.osVersion),
          SizedBox(height: 20),
          if (device.capabilities.isNotEmpty) ...[
            Text(
              'CAPABILITIES',
              style: TextStyle(color: Colors.white54, fontSize: 12),
            ),
            SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: device.capabilities
                  .map((cap) => Chip(
                        label: Text(cap.toUpperCase()),
                        backgroundColor: Colors.cyan.withValues(alpha: 0.2),
                        labelStyle: TextStyle(color: Colors.cyan, fontSize: 12),
                      ))
                  .toList(),
            ),
          ],
          SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.white54)),
          Text(value, style: TextStyle(color: Colors.white)),
        ],
      ),
    );
  }

  void _showAddDeviceDialog() {
    final nameController = TextEditingController();
    String selectedType = 'phone';
    String selectedPlatform = 'android';

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: _panel,
          title: Text('Add Device', style: TextStyle(color: Colors.cyan)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  hintText: 'Device name',
                  hintStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.cyan),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.white24),
                  ),
                ),
              ),
              SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedType,
                dropdownColor: _panel,
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Type',
                  labelStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.cyan),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.white24),
                  ),
                ),
                items: ['phone', 'pc', 'laptop', 'cctv', 'smart-home']
                    .map((t) => DropdownMenuItem(value: t, child: Text(t.toUpperCase())))
                    .toList(),
                onChanged: (v) => setDialogState(() => selectedType = v!),
              ),
              SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedPlatform,
                dropdownColor: _panel,
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Platform',
                  labelStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.cyan),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.white24),
                  ),
                ),
                items: ['android', 'ios', 'windows', 'linux']
                    .map((p) => DropdownMenuItem(value: p, child: Text(p.toUpperCase())))
                    .toList(),
                onChanged: (v) => setDialogState(() => selectedPlatform = v!),
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
                  await widget.deviceService?.addDevice(
                    name: nameController.text,
                    type: selectedType,
                    platform: selectedPlatform,
                  );
                  Navigator.pop(context);
                }
              },
              child: Text('Add', style: TextStyle(color: Colors.cyan)),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmRemove(Device device) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: _panel,
        title: Text('Remove Device', style: TextStyle(color: Colors.red)),
        content: Text(
          'Remove ${device.name}?',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel', style: TextStyle(color: Colors.white70)),
          ),
          TextButton(
            onPressed: () async {
              await widget.deviceService?.removeDevice(device.id);
              Navigator.pop(context);
            },
            child: Text('Remove', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}
