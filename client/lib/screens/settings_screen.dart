import 'dart:io' show Platform;
import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import '../services/voice_profile_service.dart';
import '../services/voice_service.dart';
import '../services/settings_service.dart';
import '../services/server_config.dart';
import 'specs_check_screen.dart';
import '../utils/theme.dart';

const _bg = AppTheme.bg;
const _panel = AppTheme.panel;

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  VoiceProfileService? _profileService;
  SettingsService? _settingsService;
  bool _loaded = false;
  bool _configMissing = false;

  bool _darkMode = true;
  bool _notificationsEnabled = true;
  bool _wakeWordEnabled = true;
  bool _healthAlerts = false;
  bool _heartRateAlerts = true;
  bool _spo2Alerts = true;
  String _wakeWord = 'Hey Jarvis';
  String _llmModel = 'llama3.2';
  String _mqttBroker = '';
  int _mqttPort = 1883;

  List _profiles = [];
  List<String> _microphones = [];
  List<String> _speakers = [];
  String _selectedMic = '';
  String _selectedSpeaker = '';
  bool _loadingDevices = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final config = await ServerConfig.load();
    if (config != null) {
      _profileService = VoiceProfileService(baseUrl: config.baseUrl);
      _settingsService = SettingsService(config);
      try {
        await _settingsService!.fetch();
        setState(() {
          _darkMode = _settingsService!.darkMode;
          _notificationsEnabled = _settingsService!.notificationsEnabled;
          _wakeWordEnabled = _settingsService!.wakeWordEnabled;
          _healthAlerts = _settingsService!.healthAlertsEnabled;
          _heartRateAlerts = _settingsService!.heartRateAlerts;
          _spo2Alerts = _settingsService!.spo2Alerts;
          _llmModel = _settingsService!.llmModel;
          _mqttBroker = _settingsService!.mqttBroker;
          _mqttPort = _settingsService!.mqttPort;
          _loaded = true;
        });
      } catch (_) {
        setState(() => _loaded = true);
      }
    } else {
      setState(() { _loaded = true; _configMissing = true; });
    }
    _loadProfiles();
    _loadAudioDevices();
  }

  Future<void> _patch(Map<String, dynamic> partial) async {
    try {
      await _settingsService?.patch(partial);
    } catch (_) {}
  }

  Future<void> _loadProfiles() async {
    if (_profileService == null) return;
    try {
      final profiles = await _profileService!.getProfiles();
      setState(() => _profiles = profiles);
    } catch (_) {}
  }

  Future<void> _loadAudioDevices() async {
    _selectedMic = VoiceService.selectedMic;
    _selectedSpeaker = VoiceService.selectedSpeaker;
    if (Platform.isAndroid) {
      if (mounted) {
        setState(() {
          _microphones = ['Default (Phone)'];
          _speakers = ['Default (Phone)'];
          _loadingDevices = false;
          if (_selectedMic.isEmpty) _selectedMic = 'Default (Phone)';
        });
      }
      return;
    }
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
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('Settings', style: TextStyle(color: Colors.cyan)),
      ),
      body: _loaded && _configMissing
          ? Center(child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.cloud_off, color: Colors.white38, size: 48),
                SizedBox(height: 16),
                Text('No server configured', style: TextStyle(color: Colors.white38)),
                SizedBox(height: 8),
                Text('Run onboarding or check connection', style: TextStyle(color: Colors.white24, fontSize: 12)),
              ],
            ))
          : _loaded
          ? ListView(
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
                    _patch({'ui': {'dark_mode': v}});
                  }),
                  _buildSwitchTile(Icons.notifications, 'Notifications', 'Enable push notifications', _notificationsEnabled, (v) {
                    setState(() => _notificationsEnabled = v);
                    _patch({'ui': {'notifications_enabled': v}});
                  }),
                ]),
                SizedBox(height: 16),
                _buildSection('Voice', [
                  _buildSwitchTile(Icons.mic, 'Voice Input', 'Enable voice commands', _wakeWordEnabled, (v) {
                    setState(() => _wakeWordEnabled = v);
                    _patch({'voice': {'wake_word_enabled': v}});
                  }),
                  _buildTapTile(Icons.record_voice_over, 'TTS Voice',
                      _profiles.isNotEmpty
                          ? '${_profiles.firstWhere((p) => p['is_active'] == true, orElse: () => _profiles.isNotEmpty ? _profiles[0] : {'name': 'None'})['name']}'
                          : 'Loading...',
                      () => _showVoicePicker()),
                ]),
                SizedBox(height: 16),
                _buildSection('AI', [
                  _buildTapTile(Icons.smart_toy, 'LLM Model', _llmModel, () => _showModelPicker()),
                ]),
                SizedBox(height: 16),
                _buildSection('Health Monitoring', [
                  _buildSwitchTile(Icons.favorite, 'Health Alerts', 'Get alerts for abnormal vitals', _healthAlerts, (v) {
                    setState(() => _healthAlerts = v);
                    _patch({'health': {'alerts_enabled': v}});
                  }),
                  _buildSwitchTile(Icons.warning_amber, 'Heart Rate Alerts', 'Alert on abnormal heart rate', _heartRateAlerts, (v) {
                    setState(() => _heartRateAlerts = v);
                    _patch({'health': {'heart_rate_alerts': v}});
                  }),
                  _buildSwitchTile(Icons.air, 'SpO2 Alerts', 'Alert on low oxygen', _spo2Alerts, (v) {
                    setState(() => _spo2Alerts = v);
                    _patch({'health': {'spo2_alerts': v}});
                  }),
                ]),
                SizedBox(height: 16),
                _buildSection('Smart Home', [
                  _buildTapTile(Icons.hub, 'MQTT Broker', _mqttBroker.isEmpty ? 'Not configured' : _mqttBroker, () => _showMQTTDialog()),
                ]),
                SizedBox(height: 16),
                _buildSection('Server', [
                  FutureBuilder<ServerConfig?>(
                    future: ServerConfig.load(),
                    builder: (context, snapshot) {
                      final config = snapshot.data;
                      final url = config?.baseUrl ?? 'Not configured';
                      final profile = config?.profileName ?? 'default';
                      return Column(
                        children: [
                          _buildTapTile(Icons.link, 'Server URL', url, () {}),
                          _buildTapTile(Icons.person, 'Profile', profile, () {}),
                          _buildTapTile(Icons.wifi, 'Connection', config?.token != null ? 'Connected' : 'Not logged in', () {}),
                        ],
                      );
                    },
                  ),
                ]),
                SizedBox(height: 16),
                if (Platform.isWindows || Platform.isLinux || Platform.isMacOS)
                  _buildSection('Desktop', [
                    _buildTapTile(Icons.picture_in_picture, 'Overlay Mode', 'Compact floating window', () {
                      windowManager.setSize(Size(240, 320));
                      windowManager.setAlwaysOnTop(true);
                      windowManager.setTitleBarStyle(TitleBarStyle.hidden);
                      windowManager.setResizable(false);
                    }),
                    _buildTapTile(Icons.close_fullscreen, 'Exit Overlay', 'Restore main window', () {
                      windowManager.setSize(Size(420, 820));
                      windowManager.setAlwaysOnTop(false);
                      windowManager.setTitleBarStyle(TitleBarStyle.normal);
                      windowManager.setResizable(true);
                      windowManager.center();
                    }),
                  ]),
                _buildSection('About', [
                  _buildTapTile(Icons.info, 'Version', '1.0.0 (MVP)', () {}),
                  _buildTapTile(Icons.dns, 'System Info', 'Hardware & config', () {
                    Navigator.push(context, MaterialPageRoute(
                      builder: (_) => SpecsCheckScreen(),
                    ));
                  }),
                  _buildTapTile(Icons.code, 'Open Source Licenses', '', () {}),
                ]),
                SizedBox(height: 32),
              ],
            )
          : Center(child: CircularProgressIndicator(color: Colors.cyan)),
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
            color: _panel,
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
      backgroundColor: _panel,
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

  void _showVoicePicker() {
    if (_profileService == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Not connected to server'), backgroundColor: Colors.red),
      );
      return;
    }
    if (_profiles.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No voice profiles loaded'), backgroundColor: Colors.red),
      );
      return;
    }
    showModalBottomSheet(
      context: context,
      backgroundColor: _panel,
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
                  await _profileService!.switchProfile(profile['id']);
                  if (mounted) {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Voice changed to ${profile['name']}'), backgroundColor: Colors.cyan),
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
    final models = ['llama3.2', 'phi4-mini', 'gemma4:e2b', 'llama3.1', 'llava:7b', 'mistral', 'codellama'];
    showModalBottomSheet(
      context: context,
      backgroundColor: _panel,
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
                _patch({'voice': {'llm_model': model}});
                Navigator.pop(context);
              },
            )),
          ],
        ),
      ),
    );
  }

  void _showMQTTDialog() {
    final brokerController = TextEditingController(text: _mqttBroker);
    final portController = TextEditingController(text: _mqttPort.toString());
    final userController = TextEditingController();
    final passController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: _panel,
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
          TextButton(onPressed: () {
            final broker = brokerController.text.trim();
            final port = int.tryParse(portController.text.trim()) ?? 1883;
            setState(() {
              _mqttBroker = broker;
              _mqttPort = port;
            });
            _patch({'smart_home': {'mqtt_broker': broker, 'mqtt_port': port}});
            Navigator.pop(context);
          }, child: Text('Save', style: TextStyle(color: Colors.cyan))),
        ],
      ),
    );
  }
}
