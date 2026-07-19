import 'package:flutter/material.dart';
import '../services/voice_profile_service.dart';
import '../services/voice_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final VoiceProfileService _profileService = VoiceProfileService();
  bool _voiceEnabled = true;
  bool _autoConnect = true;
  bool _notificationsEnabled = true;
  bool _healthAlerts = true;
  bool _darkMode = true;
  String _wakeWord = 'Hey Jarvis';
  String _llmModel = 'llama3.2';
  String _serverUrl = 'ws://localhost:8000/ws';
  List _profiles = [];

  List<String> _microphones = [];
  List<String> _speakers = [];
  String _selectedMic = '';
  String _selectedSpeaker = '';
  bool _loadingDevices = true;

  @override
  void initState() {
    super.initState();
    _loadProfiles();
    _loadAudioDevices();
  }

  Future<void> _loadProfiles() async {
    final profiles = await _profileService.getProfiles();
    setState(() => _profiles = profiles);
  }

  Future<void> _loadAudioDevices() async {
    _selectedMic = VoiceService.selectedMic;
    _selectedSpeaker = VoiceService.selectedSpeaker;

    final mics = await VoiceService.listMicrophones();
    final speakers = await VoiceService.listSpeakers();

    if (mounted) {
      setState(() {
        _microphones = mics;
        _speakers = speakers;
        _loadingDevices = false;
        if (_selectedMic.isEmpty && mics.isNotEmpty) {
          _selectedMic = mics.first;
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('Settings', style: TextStyle(color: Colors.cyan)),
      ),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          _buildSection('Audio Devices', [
            _buildDeviceTile(
              Icons.mic,
              'Microphone',
              _selectedMic.isEmpty ? 'Not selected' : _selectedMic,
              _microphones,
              _selectedMic,
              (value) async {
                setState(() => _selectedMic = value);
                await VoiceService.saveDeviceSettings(_selectedMic, _selectedSpeaker);
              },
            ),
            _buildDeviceTile(
              Icons.speaker,
              'Audio Output',
              _selectedSpeaker.isEmpty ? 'Default' : _selectedSpeaker,
              _speakers,
              _selectedSpeaker,
              (value) async {
                setState(() => _selectedSpeaker = value);
                await VoiceService.saveDeviceSettings(_selectedMic, _selectedSpeaker);
              },
            ),
          ]),
          SizedBox(height: 16),
          _buildSection('General', [
            _buildSwitchTile(Icons.dark_mode, 'Dark Mode', 'Use dark theme', _darkMode, (v) {
              setState(() => _darkMode = v);
            }),
            _buildSwitchTile(Icons.notifications, 'Notifications', 'Enable push notifications', _notificationsEnabled, (v) {
              setState(() => _notificationsEnabled = v);
            }),
          ]),
          SizedBox(height: 16),
          _buildSection('Connection', [
            _buildTapTile(Icons.wifi, 'Server URL', _serverUrl, () => _showEditDialog('Server URL', _serverUrl, (v) {
              setState(() => _serverUrl = v);
            })),
            _buildSwitchTile(Icons.link, 'Auto-Connect', 'Connect on app start', _autoConnect, (v) {
              setState(() => _autoConnect = v);
            }),
          ]),
          SizedBox(height: 16),
          _buildSection('Voice', [
            _buildSwitchTile(Icons.mic, 'Voice Input', 'Enable voice commands', _voiceEnabled, (v) {
              setState(() => _voiceEnabled = v);
            }),
            _buildTapTile(Icons.record_voice_over, 'Wake Word', _wakeWord, () => _showEditDialog('Wake Word', _wakeWord, (v) {
              setState(() => _wakeWord = v);
            })),
            _buildTapTile(Icons.record_voice_over, 'TTS Voice', _profiles.isNotEmpty ? '${_profiles.firstWhere((p) => p['is_active'] == true, orElse: () => _profiles.isNotEmpty ? _profiles[0] : {'name': 'None'})['name']}' : 'Loading...', () => _showVoicePicker()),
          ]),
          SizedBox(height: 16),
          _buildSection('AI', [
            _buildTapTile(Icons.smart_toy, 'LLM Model', _llmModel, () => _showModelPicker()),
          ]),
          SizedBox(height: 16),
          _buildSection('Health Monitoring', [
            _buildSwitchTile(Icons.favorite, 'Health Alerts', 'Get alerts for abnormal vitals', _healthAlerts, (v) {
              setState(() => _healthAlerts = v);
            }),
            _buildTapTile(Icons.warning_amber, 'Heart Rate Alerts', '50-120 bpm', () {}),
            _buildTapTile(Icons.air, 'SpO2 Alerts', 'Below 90%', () {}),
          ]),
          SizedBox(height: 16),
          _buildSection('Smart Home', [
            _buildTapTile(Icons.hub, 'MQTT Broker', 'Configure MQTT connection', () => _showMQTTDialog()),
          ]),
          SizedBox(height: 16),
          _buildSection('About', [
            _buildTapTile(Icons.info, 'Version', '1.0.0 (MVP)', () {}),
            _buildTapTile(Icons.code, 'Open Source Licenses', '', () {}),
          ]),
          SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: TextStyle(color: Colors.cyan, fontSize: 14, fontWeight: FontWeight.bold)),
        SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Color(0xFF1a1a2e),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildSwitchTile(IconData icon, String title, String subtitle, bool value, ValueChanged<bool> onChanged) {
    return SwitchListTile(
      secondary: Icon(icon, color: Colors.white70),
      title: Text(title, style: TextStyle(color: Colors.white)),
      subtitle: Text(subtitle, style: TextStyle(color: Colors.white38, fontSize: 12)),
      value: value,
      onChanged: onChanged,
      activeColor: Colors.cyan,
    );
  }

  Widget _buildTapTile(IconData icon, String title, String trailing, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: Colors.white70),
      title: Text(title, style: TextStyle(color: Colors.white)),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (trailing.isNotEmpty)
            Flexible(
              child: Text(trailing, style: TextStyle(color: Colors.white38, fontSize: 12), overflow: TextOverflow.ellipsis),
            ),
          SizedBox(width: 4),
          Icon(Icons.chevron_right, color: Colors.white38, size: 20),
        ],
      ),
      onTap: onTap,
    );
  }

  Widget _buildDeviceTile(
    IconData icon,
    String title,
    String currentDevice,
    List<String> devices,
    String selected,
    ValueChanged<String> onSelected,
  ) {
    return ListTile(
      leading: Icon(icon, color: Colors.white70),
      title: Text(title, style: TextStyle(color: Colors.white)),
      subtitle: Text(
        _loadingDevices ? 'Scanning...' : currentDevice,
        style: TextStyle(color: Colors.white38, fontSize: 12),
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_loadingDevices)
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.cyan),
            )
          else ...[
            Icon(Icons.chevron_right, color: Colors.white38, size: 20),
          ],
        ],
      ),
      onTap: _loadingDevices ? null : () => _showDevicePicker(title, devices, selected, onSelected),
    );
  }

  void _showDevicePicker(String title, List<String> devices, String current, ValueChanged<String> onSelected) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Select $title', style: TextStyle(color: Colors.cyan, fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            if (devices.isEmpty)
              Padding(
                padding: EdgeInsets.all(16),
                child: Text('No devices found', style: TextStyle(color: Colors.white38)),
              )
            else
              ...devices.map((device) => ListTile(
                title: Text(device, style: TextStyle(color: Colors.white)),
                trailing: device == current ? Icon(Icons.check, color: Colors.cyan) : null,
                onTap: () {
                  onSelected(device);
                  Navigator.pop(context);
                },
              )),
            SizedBox(height: 8),
            ListTile(
              title: Text('Refresh', style: TextStyle(color: Colors.cyan)),
              leading: Icon(Icons.refresh, color: Colors.cyan),
              onTap: () {
                Navigator.pop(context);
                _loadAudioDevices();
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showEditDialog(String title, String currentValue, ValueChanged<String> onSave) {
    final controller = TextEditingController(text: currentValue);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1a1a2e),
        title: Text(title, style: TextStyle(color: Colors.cyan)),
          content: TextField(
          controller: controller,
          style: TextStyle(color: Colors.white),
          decoration: InputDecoration(
            focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
            enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Cancel', style: TextStyle(color: Colors.white70))),
          TextButton(onPressed: () { onSave(controller.text); Navigator.pop(context); }, child: Text('Save', style: TextStyle(color: Colors.cyan))),
        ],
      ),
    );
  }

  void _showVoicePicker() {
    if (_profiles.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No voice profiles loaded'), backgroundColor: Colors.red),
      );
      return;
    }

    showModalBottomSheet(
      context: context,
      backgroundColor: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Select Voice', style: TextStyle(color: Colors.cyan, fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            ..._profiles.map((profile) {
              final isActive = profile['is_active'] == true;
              return ListTile(
                title: Text(profile['name'] ?? profile['id'], style: TextStyle(color: Colors.white)),
                subtitle: Text(profile['voice'] ?? '', style: TextStyle(color: Colors.white38, fontSize: 12)),
                trailing: isActive ? Icon(Icons.check, color: Colors.cyan) : null,
                onTap: () async {
                  final result = await _profileService.switchProfile(profile['id']);
                  if (mounted) {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Voice changed to ${profile['name']}'),
                        backgroundColor: Colors.cyan,
                      ),
                    );
                    _loadProfiles();
                  }
                },
              );
            }),
          ],
        ),
      ),
    );
  }

  void _showModelPicker() {
    final models = ['llama3.2', 'llama3.1', 'llava:7b', 'mistral', 'codellama'];

    showModalBottomSheet(
      context: context,
      backgroundColor: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Select LLM Model', style: TextStyle(color: Colors.cyan, fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            ...models.map((model) => ListTile(
              title: Text(model, style: TextStyle(color: Colors.white)),
              trailing: _llmModel == model ? Icon(Icons.check, color: Colors.cyan) : null,
              onTap: () {
                setState(() => _llmModel = model);
                Navigator.pop(context);
              },
            )),
          ],
        ),
      ),
    );
  }

  void _showMQTTDialog() {
    final brokerController = TextEditingController(text: 'localhost');
    final portController = TextEditingController(text: '1883');
    final userController = TextEditingController();
    final passController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1a1a2e),
        title: Text('MQTT Configuration', style: TextStyle(color: Colors.cyan)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: brokerController,
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Broker Address',
                  labelStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                ),
              ),
              SizedBox(height: 12),
              TextField(
                controller: portController,
                style: TextStyle(color: Colors.white),
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: 'Port',
                  labelStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                ),
              ),
              SizedBox(height: 12),
              TextField(
                controller: userController,
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Username (optional)',
                  labelStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                ),
              ),
              SizedBox(height: 12),
              TextField(
                controller: passController,
                style: TextStyle(color: Colors.white),
                obscureText: true,
                decoration: InputDecoration(
                  labelText: 'Password (optional)',
                  labelStyle: TextStyle(color: Colors.white54),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Cancel', style: TextStyle(color: Colors.white70))),
          TextButton(onPressed: () { Navigator.pop(context); }, child: Text('Connect', style: TextStyle(color: Colors.cyan))),
        ],
      ),
    );
  }
}
