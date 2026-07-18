import 'package:flutter/material.dart';
import 'dart:async';
import '../widgets/avatar_widget.dart';
import '../services/websocket_service.dart';
import '../services/voice_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final WebSocketService _webSocketService = WebSocketService();
  late VoiceService _voiceService;

  String _avatarState = 'idle';
  String _lastMessage = 'Ready to assist you.';
  String _transcription = '';
  bool _isConnected = false;

  StreamSubscription? _avatarSubscription;
  StreamSubscription? _transcriptionSubscription;
  StreamSubscription? _responseSubscription;

  @override
  void initState() {
    super.initState();
    _voiceService = VoiceService(_webSocketService);
    _setupListeners();
    _connectToServer();
  }

  void _setupListeners() {
    _avatarSubscription = _voiceService.avatarState.listen((state) {
      setState(() => _avatarState = state);
    });

    _transcriptionSubscription = _voiceService.transcription.listen((text) {
      setState(() {
        _transcription = text;
        _lastMessage = 'You said: $text';
      });
    });

    _responseSubscription = _voiceService.response.listen((response) {
      setState(() => _lastMessage = response);
    });
  }

  void _connectToServer() {
    _webSocketService.connect('ws://localhost:8000/ws');
    _webSocketService.messages.listen((message) {
      if (message['type'] == 'pong') {
        setState(() => _isConnected = true);
      }
    });

    Timer.periodic(Duration(seconds: 30), (timer) {
      if (_isConnected) {
        _webSocketService.send({'type': 'ping'});
      }
    });
  }

  @override
  void dispose() {
    _avatarSubscription?.cancel();
    _transcriptionSubscription?.cancel();
    _responseSubscription?.cancel();
    _webSocketService.dispose();
    _voiceService.dispose();
    super.dispose();
  }

  Future<void> _toggleVoice() async {
    if (_voiceService.isRecording) {
      await _voiceService.stopListening();
    } else {
      await _voiceService.startListening();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      body: SafeArea(
        child: Column(
          children: [
            _buildStatusBar(),
            Expanded(
              child: Center(
                child: AvatarWidget(currentState: _avatarState),
              ),
            ),
            _buildBottomPanel(),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBar() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _isConnected ? Colors.green : Colors.red,
                ),
              ),
              SizedBox(width: 8),
              Text(
                _isConnected ? 'Connected' : 'Disconnected',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          Text(
            'J.A.R.V.I.S.',
            style: TextStyle(
              color: Colors.cyan,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomPanel() {
    return Container(
      padding: EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          if (_transcription.isNotEmpty)
            Container(
              padding: EdgeInsets.all(12),
              margin: EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: Colors.cyan.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                _transcription,
                style: TextStyle(color: Colors.white70, fontSize: 14),
                textAlign: TextAlign.center,
              ),
            ),
          Text(
            _lastMessage,
            style: TextStyle(color: Colors.white70, fontSize: 16),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildActionButton(
                Icons.mic,
                'Voice',
                _toggleVoice,
                isActive: _voiceService.isRecording,
                activeColor: Colors.green,
              ),
              _buildActionButton(Icons.screen_share, 'Screen', () {}),
              _buildActionButton(Icons.chat, 'Text', _showTextInput),
              _buildActionButton(Icons.settings, 'Settings', () {}),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(
    IconData icon,
    String label,
    VoidCallback onTap, {
    bool isActive = false,
    Color activeColor = Colors.cyan,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isActive
                  ? activeColor.withValues(alpha: 0.3)
                  : Colors.cyan.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(16),
              border: isActive
                  ? Border.all(color: activeColor, width: 2)
                  : null,
            ),
            child: Icon(
              icon,
              color: isActive ? activeColor : Colors.cyan,
              size: 28,
            ),
          ),
          SizedBox(height: 8),
          Text(label, style: TextStyle(color: Colors.white70)),
        ],
      ),
    );
  }

  void _showTextInput() {
    final controller = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1a1a2e),
        title: Text('Send Message', style: TextStyle(color: Colors.cyan)),
        content: TextField(
          controller: controller,
          style: TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'Type your message...',
            hintStyle: TextStyle(color: Colors.white54),
            focusedBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.cyan),
            ),
            enabledBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.white24),
            ),
          ),
          autofocus: true,
          onSubmitted: (text) {
            if (text.isNotEmpty) {
              _voiceService.sendTextMessage(text);
              Navigator.pop(context);
            }
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel', style: TextStyle(color: Colors.white70)),
          ),
          TextButton(
            onPressed: () {
              if (controller.text.isNotEmpty) {
                _voiceService.sendTextMessage(controller.text);
                Navigator.pop(context);
              }
            },
            child: Text('Send', style: TextStyle(color: Colors.cyan)),
          ),
        ],
      ),
    );
  }
}
