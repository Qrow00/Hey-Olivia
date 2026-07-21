import 'package:flutter/material.dart';
import 'dart:async';
import '../widgets/avatar_widget.dart';
import '../services/websocket_service.dart';
import '../services/voice_service.dart';

class HomeScreen extends StatefulWidget {
  final WebSocketService webSocketService;
  const HomeScreen({super.key, required this.webSocketService});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late VoiceService _voiceService;

  String _avatarState = 'idle';
  String _lastMessage = 'Ready to assist you.';
  String _transcription = '';
  bool _isConnected = false;
  bool _wordPulse = false;
  bool _isListening = false;

  StreamSubscription? _avatarSubscription;
  StreamSubscription? _transcriptionSubscription;
  StreamSubscription? _responseSubscription;
  StreamSubscription? _vadSubscription;
  Timer? _wordPulseTimer;
  int _wordIndex = 0;
  List<String> _words = [];

  @override
  void initState() {
    super.initState();
    _voiceService = VoiceService(widget.webSocketService);
    _setupListeners();
    _setupConnectionWatch();
    _autoStartListening();
  }

  void _autoStartListening() async {
    await Future.delayed(Duration(seconds: 2));
    if (mounted && !_isListening) {
      final started = await _voiceService.startListening();
      if (mounted) {
        setState(() => _isListening = started);
      }
    }
  }

  void _setupListeners() {
    _avatarSubscription = _voiceService.avatarState.listen((state) {
      setState(() => _avatarState = state);
      if (state == 'speaking') {
        _startWordPulse();
      } else {
        _stopWordPulse();
      }
    });

    _transcriptionSubscription = _voiceService.transcription.listen((text) {
      setState(() {
        _transcription = text;
        _lastMessage = 'You said: $text';
      });
    });

    _responseSubscription = _voiceService.response.listen((response) {
      setState(() => _lastMessage = response);
      _words = response.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).toList();
      _wordIndex = 0;
      if (_avatarState == 'speaking') {
        _startWordPulse();
      }
    });

    _vadSubscription = _voiceService.vadState.listen((state) {
      if (mounted) {
        setState(() => _isListening = state != VadState.idle);
      }
    });
  }

  void _startWordPulse() {
    _stopWordPulse();
    if (_words.isEmpty) return;

    _wordPulseTimer = Timer.periodic(Duration(milliseconds: 150), (timer) {
      if (!mounted || _avatarState != 'speaking') {
        _stopWordPulse();
        return;
      }

      if (_wordIndex < _words.length) {
        setState(() {
          _wordPulse = !_wordPulse;
        });
        _wordIndex++;
      } else {
        _stopWordPulse();
      }
    });
  }

  void _stopWordPulse() {
    _wordPulseTimer?.cancel();
    _wordPulseTimer = null;
  }

  void _setupConnectionWatch() {
    setState(() => _isConnected = widget.webSocketService.isConnected);

    widget.webSocketService.messages.listen((_) {
      if (!_isConnected) {
        setState(() => _isConnected = true);
        if (!_isListening) _autoStartListening();
      }
    });

    Timer.periodic(Duration(seconds: 2), (timer) {
      if (mounted) {
        final connected = widget.webSocketService.isConnected;
        if (connected != _isConnected) {
          setState(() => _isConnected = connected);
          if (connected && !_isListening) _autoStartListening();
        }
      } else {
        timer.cancel();
      }
    });
  }

  @override
  void dispose() {
    _stopWordPulse();
    _avatarSubscription?.cancel();
    _transcriptionSubscription?.cancel();
    _responseSubscription?.cancel();
    _vadSubscription?.cancel();
    _voiceService.dispose();
    super.dispose();
  }

  Future<void> _toggleListening() async {
    if (_isListening) {
      await _voiceService.stopListening();
      setState(() => _isListening = false);
    } else {
      final started = await _voiceService.startListening();
      setState(() => _isListening = started);
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
                child: AvatarWidget(
                  currentState: _avatarState,
                  wordPulse: _wordPulse,
                ),
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
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _isListening ? Colors.green : Colors.grey,
                ),
              ),
              SizedBox(width: 6),
              Text(
                _isListening ? 'Listening' : 'Muted',
                style: TextStyle(
                  color: _isListening ? Colors.green : Colors.grey,
                  fontSize: 12,
                ),
              ),
              SizedBox(width: 12),
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
        ],
      ),
    );
  }

  Widget _buildBottomPanel() {
    String statusText;
    switch (_avatarState) {
      case 'listening':
        statusText = 'Listening...';
        break;
      case 'thinking':
        statusText = 'Processing...';
        break;
      case 'speaking':
        statusText = 'Speaking...';
        break;
      case 'error':
        statusText = 'Something went wrong. Try again.';
        break;
      default:
        statusText = _lastMessage;
    }

    return Container(
      padding: EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          Text(
            statusText,
            style: TextStyle(
              color: _avatarState == 'speaking' ? Colors.cyan : Colors.white54,
              fontSize: 16,
              fontStyle: _avatarState == 'idle' ? FontStyle.normal : FontStyle.italic,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildMicButton(),
              _buildActionButton(Icons.chat, 'Type', _showTextInput),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMicButton() {
    final isActive = _isListening;
    final color = isActive ? Colors.green : Colors.red;

    return GestureDetector(
      onTap: _toggleListening,
      child: Column(
        children: [
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: color, width: 2),
            ),
            child: Icon(
              isActive ? Icons.mic : Icons.mic_off,
              color: color,
              size: 28,
            ),
          ),
          SizedBox(height: 8),
          Text(
            isActive ? 'Listening' : 'Muted',
            style: TextStyle(color: Colors.white70),
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
        title: Text('Speak to J.A.R.V.I.S.', style: TextStyle(color: Colors.cyan)),
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
