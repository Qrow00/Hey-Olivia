import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'services/websocket_service.dart';
import 'services/audio_service.dart';
import 'models/api_models.dart';
import 'widgets/avatar_widget.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const JARVISApp());
}

class JARVISApp extends StatefulWidget {
  const JARVISApp({super.key});

  @override
  State<JARVISApp> createState() => _JARVISAppState();
}

class _JARVISAppState extends State<JARVISApp> {
  late JarvisWebSocketService _wsService;
  late AudioService _audioService;
  
  bool _isConnected = false;
  String _lastResponse = 'Waiting for J.A.R.V.I.S...';
  AvatarState _avatarState = AvatarState.idle;
  bool _isListening = false;
  String _statusMessage = 'Tap mic to speak';

  @override
  void initState() {
    super.initState();
    _initServices();
  }

  Future<void> _initServices() async {
    _audioService = AudioService();
    await _audioService.initialize();

    _wsService = JarvisWebSocketService(
      serverUrl: 'ws://10.0.2.2:8000/ws',
      token: '',
    );

    // Connect WebSocket
    await _wsService.connect();

    // Listen for messages
    _wsService.messageStream.listen((message) {
      _processMessage(message);
    });
  }

  void _processMessage(dynamic message) {
    if (message is! Map<String, dynamic>) return;

    final type = message['type'] as String? ?? '';

    setState(() {
      switch (type) {
        case 'voice_status':
          _isListening = message['is_listening'] as bool? ?? false;
          _statusMessage = message['wake_detected'] == true 
              ? 'Wake word detected!' 
              : 'Listening...';
          _avatarState = _isListening ? AvatarState.listening : AvatarState.idle;
          break;

        case 'command_result':
          final success = message['success'] as bool? ?? false;
          _lastResponse = message['result_text'] as String? ?? 'Command processed';
          _avatarState = AvatarState.thinking;
          break;

        case 'response':
          final text = message['text'] as String? ?? '';
          _lastResponse = text;
          _avatarState = AvatarState.speaking;
          // TODO: Play audio from message['audioBase64']
          break;

        case 'avatar_state':
          final stateStr = message['state'] as String? ?? 'idle';
          _avatarState = AvatarState.values.firstWhere(
            (e) => e.value == stateStr,
            orElse: () => AvatarState.idle,
          );
          break;

        case 'settings_updated':
          // Profile settings updated
          break;

        case 'plugin_status':
          // Plugin enabled/disabled
          break;

        case 'profile_switched':
          // Profile changed
          break;

        case 'error':
          _avatarState = AvatarState.error;
          _lastResponse = 'Error: ${message['message']}';
          break;

        default:
          break;
      }
    });
  }

  @override
  void dispose() {
    _wsService.dispose();
    _audioService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'J.A.R.V.I.S. V3',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.deepPurple,
        scaffoldBackgroundColor: const Color(0xFF121212),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1F1F1F),
          elevation: 0,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.deepPurple,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
        ),
      ),
      home: Scaffold(
        appBar: AppBar(
          title: const Text('J.A.R.V.I.S. V3'),
          actions: [
            IconButton(
              icon: Icon(_isConnected ? Icons.wifi : Icons.wifi_off),
              onPressed: () {},
              tooltip: _isConnected ? 'Connected' : 'Disconnected',
            ),
            IconButton(
              icon: const Icon(Icons.settings),
              onPressed: _showSettings,
            ),
          ],
        ),
        body: SafeArea(
          child: Column(
            children: [
              // Avatar and status
              Expanded(
                flex: 3,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      AvatarWidget(
                        key: ValueKey(_avatarState),
                        state: _avatarState,
                        size: 160,
                      ),
                      const SizedBox(height: 24),
                      Text(
                        _statusMessage,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Colors.grey[400],
                        ),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        constraints: const BoxConstraints(maxWidth: 300),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.deepPurple[900]?.withOpacity(0.3),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.deepPurple.withOpacity(0.3)),
                        ),
                        child: SelectableText(
                          _lastResponse,
                          style: Theme.of(context).textTheme.bodyLarge,
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Voice interaction area
              Expanded(
                flex: 2,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildVoiceArea(),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _buildQuickAction(Icons.settings, 'Settings', _showSettings),
                        const SizedBox(width: 16),
                        _buildQuickAction(Icons.person, 'Profile', _switchProfile),
                        const SizedBox(width: 16),
                        _buildQuickAction(Icons.devices, 'Devices', () {}),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: 0,
          onDestinationSelected: (index) {},
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.smart_toy),
              label: 'Home',
            ),
            NavigationDestination(
              icon: Icon(Icons.monitor_heart),
              label: 'Health',
            ),
            NavigationDestination(
              icon: Icon(Icons.devices),
              label: 'Devices',
            ),
            NavigationDestination(
              icon: Icon(Icons.more_horiz),
              label: 'More',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVoiceArea() {
    return GestureDetector(
      onTapDown: _isListening ? null : (_) => _startListening(),
      onTapUp: _isListening ? (_) => _stopListening() : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: _isListening ? 140 : 100,
        height: _isListening ? 140 : 100,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(
            colors: _isListening
                ? [Colors.deepPurpleAccent, Colors.deepPurple]
                : [Colors.deepPurple[900]!, Colors.deepPurple[700]!],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          boxShadow: [
            BoxShadow(
              color: _isListening
                  ? Colors.deepPurpleAccent.withOpacity(0.5)
                  : Colors.deepPurple.withOpacity(0.3),
              blurRadius: _isListening ? 30 : 15,
              spreadRadius: _isListening ? 5 : 0,
            ),
          ],
        ),
        child: Center(
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            child: Icon(
              _isListening ? Icons.mic : Icons.mic_none,
              key: ValueKey(_isListening),
              color: Colors.white,
              size: _isListening ? 56 : 40,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildQuickAction(IconData icon, String label, VoidCallback onTap) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.deepPurple[900]?.withOpacity(0.5),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.deepPurple.withOpacity(0.3)),
            ),
            child: Icon(icon, color: Colors.white, size: 28),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey[400],
          ),
        ),
      ],
    );
  }

  Future<void> _startListening() async {
    setState(() {
      _isListening = true;
      _statusMessage = 'Listening...';
      _avatarState = AvatarState.listening;
    });

    try {
      await _audioService.startRecording(onData: (data) {
        final base64 = base64Encode(data);
        _wsService.sendVoiceChunk(base64, timestamp: DateTime.now().millisecondsSinceEpoch);
      });
    } catch (e) {
      setState(() {
        _statusMessage = 'Error: $e';
        _avatarState = AvatarState.error;
      });
    }
  }

  Future<void> _stopListening() async {
    setState(() {
      _isListening = false;
      _statusMessage = 'Processing...';
      _avatarState = AvatarState.thinking;
    });

    await _audioService.stopRecording();
  }

  void _showSettings() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1F1F1F),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Settings', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            ListTile(
              leading: const Icon(Icons.person),
              title: const Text('Profile'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.palette),
              title: const Text('Theme'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.volume_up),
              title: const Text('Voice'),
              onTap: () => Navigator.pop(context),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _switchProfile() async {
    final profiles = ['default', 'jarvis', 'friday'];
    final current = _wsService.profileSettings.profile;
    final currentIndex = profiles.indexOf(current);
    final nextIndex = (currentIndex + 1) % profiles.length;
    await _wsService.switchProfile(profiles[nextIndex]);
    
    setState(() {
      _statusMessage = 'Switched to ${profiles[nextIndex]}';
    });
  }
}