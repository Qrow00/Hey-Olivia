import 'dart:async';
import 'package:flutter/material.dart';
import '../models/smart_device.dart';
import '../services/smart_home_service.dart';

class SmartHomeScreen extends StatefulWidget {
  final SmartHomeService smartHomeService;

  const SmartHomeScreen({super.key, required this.smartHomeService});

  @override
  State<SmartHomeScreen> createState() => _SmartHomeScreenState();
}

class _SmartHomeScreenState extends State<SmartHomeScreen> {
  StreamSubscription? _deviceSubscription;
  String _selectedRoom = 'All';
  List<String> _rooms = ['All'];

  @override
  void initState() {
    super.initState();
    _loadDevices();
    _setupListeners();
  }

  void _loadDevices() async {
    await widget.smartHomeService.fetchDevices();
    final rooms = await widget.smartHomeService.fetchRooms();
    setState(() {
      _rooms = ['All', ...rooms];
    });
  }

  void _setupListeners() {
    _deviceSubscription = widget.smartHomeService.deviceUpdates.listen((device) {
      if (mounted) setState(() {});
    });
  }

  List<SmartDevice> get _filteredDevices {
    if (_selectedRoom == 'All') return widget.smartHomeService.allDevices;
    return widget.smartHomeService.allDevices.where((d) => d.room == _selectedRoom).toList();
  }

  @override
  void dispose() {
    _deviceSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('Smart Home', style: TextStyle(color: Colors.cyan)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: Colors.cyan),
            onPressed: _loadDevices,
          ),
          IconButton(
            icon: Icon(Icons.add, color: Colors.cyan),
            onPressed: _showAddDeviceDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildRoomFilter(),
          Expanded(
            child: _filteredDevices.isEmpty
                ? _buildNoDevices()
                : _buildDeviceGrid(),
          ),
        ],
      ),
    );
  }

  Widget _buildRoomFilter() {
    return Container(
      height: 50,
      padding: EdgeInsets.symmetric(horizontal: 16),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: _rooms.length,
        itemBuilder: (context, index) {
          final room = _rooms[index];
          final isSelected = _selectedRoom == room;
          return Padding(
            padding: EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(room),
              selected: isSelected,
              selectedColor: Colors.cyan,
              backgroundColor: Color(0xFF1a1a2e),
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : Colors.white70,
                fontSize: 12,
              ),
              onSelected: (selected) {
                setState(() => _selectedRoom = room);
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildNoDevices() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.home_outlined, size: 64, color: Colors.white24),
          SizedBox(height: 16),
          Text('No devices found', style: TextStyle(color: Colors.white70, fontSize: 18)),
          SizedBox(height: 8),
          Text('Add smart devices to control your home', style: TextStyle(color: Colors.white38)),
          SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _showAddDeviceDialog,
            icon: Icon(Icons.add),
            label: Text('Add Device'),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.cyan),
          ),
        ],
      ),
    );
  }

  Widget _buildDeviceGrid() {
    return GridView.builder(
      padding: EdgeInsets.all(16),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 1.2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: _filteredDevices.length,
      itemBuilder: (context, index) {
        return _buildDeviceCard(_filteredDevices[index]);
      },
    );
  }

  Widget _buildDeviceCard(SmartDevice device) {
    return GestureDetector(
      onTap: () => _showDeviceControls(device),
      child: Container(
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: device.isOn
              ? Colors.cyan.withValues(alpha: 0.15)
              : Color(0xFF1a1a2e),
          borderRadius: BorderRadius.circular(16),
          border: device.isOn
              ? Border.all(color: Colors.cyan.withValues(alpha: 0.5))
              : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: device.isOn
                        ? Colors.cyan.withValues(alpha: 0.3)
                        : Colors.white.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    _getDeviceIcon(device.type),
                    color: device.isOn ? Colors.cyan : Colors.white54,
                    size: 24,
                  ),
                ),
                Switch(
                  value: device.isOn,
                  onChanged: (value) {
                    value ? widget.smartHomeService.turnOn(device.id)
                         : widget.smartHomeService.turnOff(device.id);
                  },
                  activeColor: Colors.cyan,
                ),
              ],
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(device.name,
                    style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                    maxLines: 1, overflow: TextOverflow.ellipsis),
                SizedBox(height: 2),
                Text(device.room.isNotEmpty ? device.room : device.type.toUpperCase(),
                    style: TextStyle(color: Colors.white54, fontSize: 11)),
              ],
            ),
            if (device.type == 'light' && device.isOn)
              Slider(
                value: device.brightness.toDouble(),
                min: 0,
                max: 100,
                onChanged: (value) {
                  widget.smartHomeService.setBrightness(device.id, value.toInt());
                },
                activeColor: Colors.cyan,
              ),
          ],
        ),
      ),
    );
  }

  IconData _getDeviceIcon(String type) {
    switch (type) {
      case 'light': return Icons.lightbulb;
      case 'switch': return Icons.toggle_on;
      case 'thermostat': return Icons.thermostat;
      case 'lock': return Icons.lock;
      case 'fan': return Icons.air;
      case 'curtain': return Icons.curtains;
      case 'sensor': return Icons.sensors;
      case 'plug': return Icons.power;
      case 'speaker': return Icons.speaker;
      case 'camera': return Icons.videocam;
      default: return Icons.device_unknown;
    }
  }

  void _showDeviceControls(SmartDevice device) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _buildControlSheet(device),
    );
  }

  Widget _buildControlSheet(SmartDevice device) {
    return StatefulBuilder(
      builder: (context, setModalState) => Padding(
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
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(device.name, style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                Switch(
                  value: device.isOn,
                  onChanged: (value) {
                    value ? widget.smartHomeService.turnOn(device.id)
                         : widget.smartHomeService.turnOff(device.id);
                    setModalState(() {});
                  },
                  activeColor: Colors.cyan,
                ),
              ],
            ),
            SizedBox(height: 16),
            if (device.type == 'light') ...[
              Text('Brightness', style: TextStyle(color: Colors.white54, fontSize: 12)),
              Slider(
                value: device.brightness.toDouble(),
                min: 0,
                max: 100,
                onChanged: (value) {
                  widget.smartHomeService.setBrightness(device.id, value.toInt());
                  setModalState(() {});
                },
                activeColor: Colors.cyan,
              ),
              SizedBox(height: 16),
              Text('Color', style: TextStyle(color: Colors.white54, fontSize: 12)),
              SizedBox(height: 8),
              _buildColorPicker(device),
            ],
            if (device.type == 'thermostat') ...[
              Text('Temperature', style: TextStyle(color: Colors.white54, fontSize: 12)),
              Slider(
                value: device.temperature,
                min: 16,
                max: 30,
                onChanged: (value) {
                  widget.smartHomeService.setTemperature(device.id, value);
                  setModalState(() {});
                },
                activeColor: Colors.cyan,
              ),
              Text('${device.temperature.toStringAsFixed(1)}°C',
                  style: TextStyle(color: Colors.white, fontSize: 24)),
            ],
            SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildColorPicker(SmartDevice device) {
    final colors = [
      '#ffffff', '#ff0000', '#00ff00', '#0000ff',
      '#ffff00', '#ff00ff', '#00ffff', '#ff8800',
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: colors.map((color) {
        final isSelected = device.color == color;
        return GestureDetector(
          onTap: () {
            widget.smartHomeService.setColor(device.id, color);
          },
          child: Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: Color(int.parse('FF${color.substring(1)}', radix: 16)),
              shape: BoxShape.circle,
              border: isSelected
                  ? Border.all(color: Colors.cyan, width: 3)
                  : null,
            ),
          ),
        );
      }).toList(),
    );
  }

  void _showAddDeviceDialog() {
    final nameController = TextEditingController();
    final ipController = TextEditingController();
    final topicController = TextEditingController();
    final roomController = TextEditingController();
    String selectedType = 'light';
    String selectedProtocol = 'mqtt';

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: Color(0xFF1a1a2e),
          title: Text('Add Device', style: TextStyle(color: Colors.cyan)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  style: TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'Device Name',
                    labelStyle: TextStyle(color: Colors.white54),
                    focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                  ),
                ),
                SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: selectedType,
                  dropdownColor: Color(0xFF1a1a2e),
                  style: TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'Type',
                    labelStyle: TextStyle(color: Colors.white54),
                    focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                  ),
                  items: [
                    'light', 'switch', 'thermostat', 'lock', 'fan',
                    'curtain', 'sensor', 'plug', 'speaker',
                  ].map((t) => DropdownMenuItem(value: t, child: Text(t.toUpperCase()))).toList(),
                  onChanged: (v) => setDialogState(() => selectedType = v!),
                ),
                SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: selectedProtocol,
                  dropdownColor: Color(0xFF1a1a2e),
                  style: TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'Protocol',
                    labelStyle: TextStyle(color: Colors.white54),
                    focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                  ),
                  items: ['mqtt', 'http', 'tasmota', 'shelly']
                      .map((p) => DropdownMenuItem(value: p, child: Text(p.toUpperCase())))
                      .toList(),
                  onChanged: (v) => setDialogState(() => selectedProtocol = v!),
                ),
                SizedBox(height: 12),
                TextField(
                  controller: ipController,
                  style: TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'IP Address (optional)',
                    labelStyle: TextStyle(color: Colors.white54),
                    focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                  ),
                ),
                SizedBox(height: 12),
                TextField(
                  controller: topicController,
                  style: TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'MQTT Topic (optional)',
                    labelStyle: TextStyle(color: Colors.white54),
                    focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                  ),
                ),
                SizedBox(height: 12),
                TextField(
                  controller: roomController,
                  style: TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'Room',
                    labelStyle: TextStyle(color: Colors.white54),
                    focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                    enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Cancel', style: TextStyle(color: Colors.white70)),
            ),
            TextButton(
              onPressed: () async {
                if (nameController.text.isNotEmpty) {
                  await widget.smartHomeService.addDevice(
                    name: nameController.text,
                    type: selectedType,
                    protocol: selectedProtocol,
                    ip: ipController.text,
                    topic: topicController.text,
                    room: roomController.text,
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
