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
  bool _wakeWordMode = false;
  VoicePhase _voicePhase = VoicePhase.wakeWord;
  final TextEditingController _chatController = TextEditingController();

  StreamSubscription? _avatarSubscription;
  StreamSubscription? _transcriptionSubscription;
  StreamSubscription? _responseSubscription;
  StreamSubscription? _vadSubscription;
  StreamSubscription? _messageSubscription;
  StreamSubscription? _ttsDoneSubscription;
  Timer? _wordPulseTimer;
  int _wordIndex = 0;
  List<String> _words = [];

  @override
  void initState() {
    super.initState();
    _voiceService = VoiceService(widget.webSocketService);
    _setupListeners();
    _setupConnectionWatch();
  }

  bool _greetingReceived = false;

  void _setupListeners() {
    _avatarSubscription = _voiceService.avatarState.listen((state) {
      setState(() {
        _avatarState = state;
        _voicePhase = _voiceService.voicePhase;
        if (state == 'idle') {
          _wakeWordMode = _voiceService.isListening;
        }
      });
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

    _ttsDoneSubscription = _voiceService.ttsDone.listen((_) {
      if (!_greetingReceived && mounted) {
        _greetingReceived = true;
        Future.delayed(Duration(milliseconds: 500), () async {
          if (mounted) {
            final started = await _voiceService.startWakeWordMode();
            if (mounted) setState(() {
              _wakeWordMode = started;
              _voicePhase = VoicePhase.wakeWord;
            });
          }
        });
      }
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
      if (mounted && _wakeWordMode) {
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

    _messageSubscription = widget.webSocketService.messages.listen((_) {
      if (!_isConnected) {
        setState(() => _isConnected = true);
      }
    });

    Timer.periodic(Duration(seconds: 2), (timer) {
      if (mounted) {
        final connected = widget.webSocketService.isConnected;
        if (connected != _isConnected) {
          setState(() => _isConnected = connected);
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
    _messageSubscription?.cancel();
    _ttsDoneSubscription?.cancel();
    _voiceService.dispose();
    super.dispose();
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
    final isCommandPhase = _voicePhase == VoicePhase.command;
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
                  color: _wakeWordMode
                      ? (isCommandPhase ? Colors.orange : Colors.green)
                      : Colors.grey,
                ),
              ),
              SizedBox(width: 6),
              Text(
                _wakeWordMode
                    ? (isCommandPhase ? 'Command' : 'Wake Word')
                    : 'Muted',
                style: TextStyle(
                  color: _wakeWordMode
                      ? (isCommandPhase ? Colors.orange : Colors.green)
                      : Colors.grey,
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
        statusText = _voicePhase == VoicePhase.command
            ? 'Listening for command...'
            : 'Listening...';
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
        if (_wakeWordMode) {
          statusText = _voicePhase == VoicePhase.command
              ? 'Command received. Speak your request...'
              : 'Say "Hey Jarvis" to activate';
        } else {
          statusText = _lastMessage;
        }
    }

    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            statusText,
            style: TextStyle(
              color: _avatarState == 'speaking' ? Colors.cyan : Colors.white54,
              fontSize: 14,
              fontStyle: _avatarState == 'idle' ? FontStyle.normal : FontStyle.italic,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          SizedBox(height: 12),
          _buildChatBar(),
        ],
      ),
    );
  }

  Widget _buildChatBar() {
    return Container(
      decoration: BoxDecoration(
        color: Color(0xFF0d1117),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: Colors.cyan.withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _chatController,
              style: TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Type a message...',
                hintStyle: TextStyle(color: Colors.white38),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (text) => _sendChat(text),
            ),
          ),
          IconButton(
            icon: Icon(Icons.send, color: Colors.cyan),
            onPressed: () => _sendChat(_chatController.text),
          ),
        ],
      ),
    );
  }

  void _sendChat(String text) {
    if (text.trim().isEmpty) return;
    _voiceService.sendTextMessage(text.trim());
    _chatController.clear();
  }
}
