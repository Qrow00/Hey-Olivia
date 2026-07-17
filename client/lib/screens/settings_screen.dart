import 'package:flutter/material.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        title: Text('Settings'),
        backgroundColor: Color(0xFF1a1a2e),
      ),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          _buildSection('General', [
            _buildSettingTile(Icons.dark_mode, 'Theme', 'Dark'),
            _buildSettingTile(Icons.language, 'Language', 'English'),
          ]),
          SizedBox(height: 16),
          _buildSection('Voice', [
            _buildSettingTile(Icons.mic, 'Voice Input', 'Enabled'),
            _buildSettingTile(Icons.record_voice_over, 'Wake Word', 'Hey Jarvis'),
          ]),
          SizedBox(height: 16),
          _buildSection('Connection', [
            _buildSettingTile(Icons.wifi, 'Server', '100.x.x.x:8000'),
            _buildSettingTile(Icons.link, 'Auto-Connect', 'Enabled'),
          ]),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            color: Colors.cyan,
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 8),
        Card(
          color: Color(0xFF1a1a2e),
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildSettingTile(IconData icon, String title, String value) {
    return ListTile(
      leading: Icon(icon, color: Colors.white70),
      title: Text(title, style: TextStyle(color: Colors.white)),
      trailing: Text(value, style: TextStyle(color: Colors.white54)),
    );
  }
}
