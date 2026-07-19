import 'package:flutter/material.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _voiceEnabled = true;
  bool _autoConnect = true;
  bool _notificationsEnabled = true;
  bool _healthAlerts = true;
  bool _darkMode = true;
  String _wakeWord = 'Hey Jarvis';
  String _ttsVoice = 'en-US-GuyNeural';
  String _llmModel = 'llama3.2';
  String _serverUrl = 'ws://localhost:8000/ws';
  double _voiceSpeed = 1.0;
  double _voicePitch = 1.0;

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
            _buildTapTile(Icons.record_voice_over, 'TTS Voice', _ttsVoice, () => _showVoicePicker()),
            _buildSliderTile(Icons.speed, 'Voice Speed', _voiceSpeed, 0.5, 2.0, (v) {
              setState(() => _voiceSpeed = v);
            }),
            _buildSliderTile(Icons.graphic_eq, 'Voice Pitch', _voicePitch, 0.5, 2.0, (v) {
              setState(() => _voicePitch = v);
            }),
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
            _buildTapTile(Icons.info, 'Version', '0.2.0 (Phase 5)', () {}),
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
    return ListTile(
      leading: Icon(icon, color: Colors.white70),
      title: Text(title, style: TextStyle(color: Colors.white)),
      subtitle: Text(subtitle, style: TextStyle(color: Colors.white38, fontSize: 12)),
      trailing: Switch(
        value: value,
        onChanged: onChanged,
        activeColor: Colors.cyan,
      ),
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
            Text(trailing, style: TextStyle(color: Colors.white38, fontSize: 12)),
          SizedBox(width: 4),
          Icon(Icons.chevron_right, color: Colors.white38, size: 20),
        ],
      ),
      onTap: onTap,
    );
  }

  Widget _buildSliderTile(IconData icon, String title, double value, double min, double max, ValueChanged<double> onChanged) {
    return ListTile(
      leading: Icon(icon, color: Colors.white70),
      title: Text(title, style: TextStyle(color: Colors.white)),
      subtitle: Slider(
        value: value,
        min: min,
        max: max,
        onChanged: onChanged,
        activeColor: Colors.cyan,
      ),
      trailing: Text(value.toStringAsFixed(1), style: TextStyle(color: Colors.white54)),
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
    final voices = [
      'en-US-GuyNeural',
      'en-US-JennyNeural',
      'en-US-AriaNeural',
      'en-GB-SoniaNeural',
      'en-AU-NatashaNeural',
    ];

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
            ...voices.map((voice) => ListTile(
              title: Text(voice, style: TextStyle(color: Colors.white)),
              trailing: _ttsVoice == voice ? Icon(Icons.check, color: Colors.cyan) : null,
              onTap: () {
                setState(() => _ttsVoice = voice);
                Navigator.pop(context);
              },
            )),
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
