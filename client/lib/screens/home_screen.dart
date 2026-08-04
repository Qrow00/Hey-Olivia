import 'package:flutter/material.dart';
import 'dart:async';
import '../widgets/avatar_widget.dart';
import '../services/websocket_service.dart';
import '../services/voice_service.dart';
import '../utils/responsive.dart';

const _bg = Color(0xFF080818);
const _panel = Color(0xFF10102a);
const _hud = Color(0xFF00e5ff);
const _hudDim = Color(0xFF0077b6);
const _text = Color(0xFFE0E0E0);
const _textDim = Color(0xFF6e7681);
const _danger = Color(0xFFFF6D00);
const _success = Color(0xFF00C853);

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
  final ScrollController _chatScrollController = ScrollController();
  List<_ChatMessage> _chatHistory = [];
  bool _chatExpanded = false;

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
      _addChatMessage('You', text, _hud);
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
      _addChatMessage('J.A.R.V.I.S.', response, _hud);
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

  void _addChatMessage(String sender, String content, Color color) {
    setState(() {
      _chatHistory.add(_ChatMessage(sender, content, DateTime.now(), color));
      if (_chatHistory.length > 50) {
        _chatHistory = _chatHistory.sublist(-50);
      }
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_chatScrollController.hasClients) {
        _chatScrollController.animateTo(
          _chatScrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
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
        setState(() => _wordPulse = !_wordPulse);
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
      if (!_isConnected) setState(() => _isConnected = true);
    });
    Timer.periodic(Duration(seconds: 2), (timer) {
      if (mounted) {
        final connected = widget.webSocketService.isConnected;
        if (connected != _isConnected) setState(() => _isConnected = connected);
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
    _chatController.dispose();
    _chatScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: SafeArea(
        child: Column(
          children: [
            _buildStatusBar(),
            Expanded(child: _buildAvatarSection()),
            _buildChatHistory(),
            _buildBottomPanel(),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBar() {
    final isCmd = _voicePhase == VoicePhase.command;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: Display.isTablet(context) ? 24 : 16, vertical: 8),
      child: Row(
        children: [
          _statusDot(_isConnected ? _success : Colors.red),
          SizedBox(width: 6),
          Text(_isConnected ? 'ONLINE' : 'OFFLINE',
              style: TextStyle(color: _isConnected ? _success : Colors.red, fontSize: 10, letterSpacing: 1.2)),
          SizedBox(width: 16),
          _statusDot(_wakeWordMode ? (isCmd ? _danger : _success) : _textDim),
          SizedBox(width: 6),
          Text(_wakeWordMode ? (isCmd ? 'CMD' : 'AWAKE') : 'CHAT',
              style: TextStyle(color: _wakeWordMode ? (isCmd ? _danger : _success) : _textDim, fontSize: 10, letterSpacing: 1.2)),
          Spacer(),
          Text('J.A.R.V.I.S.', style: TextStyle(color: _hud, fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
        ],
      ),
    );
  }

  Widget _statusDot(Color color) {
    return Container(
      width: 6, height: 6,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }

  Widget _buildAvatarSection() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 16),
      child: AspectRatio(
        aspectRatio: 1,
        child: AvatarWidget(
          currentState: _avatarState,
          wordPulse: _wordPulse,
        ),
      ),
    );
  }

  Widget _buildChatHistory() {
    if (_chatHistory.isEmpty) return SizedBox.shrink();
    return GestureDetector(
      onVerticalDragUpdate: (details) {
        if (details.delta.dy < -20) setState(() => _chatExpanded = true);
        if (details.delta.dy > 20) setState(() => _chatExpanded = false);
      },
      child: AnimatedContainer(
        duration: Duration(milliseconds: 200),
        height: _chatExpanded ? 200 : 60,
        margin: EdgeInsets.symmetric(horizontal: Display.isTablet(context) ? 48 : 12),
        decoration: BoxDecoration(
          color: _panel,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: _hud.withValues(alpha: 0.1), width: 0.5),
        ),
        child: Column(
          children: [
            Container(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              child: Row(
                children: [
                  Text('HISTORY', style: TextStyle(color: _textDim, fontSize: 9, letterSpacing: 1)),
                  Spacer(),
                  Icon(_chatExpanded ? Icons.expand_more : Icons.expand_less,
                      color: _textDim, size: 16),
                ],
              ),
            ),
            Expanded(
              child: _chatExpanded
                  ? ListView.builder(
                      controller: _chatScrollController,
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      itemCount: _chatHistory.length,
                      itemBuilder: (ctx, i) {
                        final msg = _chatHistory[i];
                        return Padding(
                          padding: EdgeInsets.only(bottom: 6),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(msg.sender == 'You' ? '>' : '#',
                                  style: TextStyle(color: msg.color, fontSize: 11)),
                              SizedBox(width: 6),
                              Expanded(
                                child: Text(msg.content,
                                    style: TextStyle(color: _text, fontSize: 12),
                                    maxLines: 3, overflow: TextOverflow.ellipsis),
                              ),
                            ],
                          ),
                        );
                      },
                    )
                  : ListView(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      children: [
                        Text(
                          _chatHistory.last.sender == 'You'
                              ? '> ${_chatHistory.last.content}'
                              : '# ${_chatHistory.last.content}',
                          style: TextStyle(color: _chatHistory.last.color, fontSize: 12),
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomPanel() {
    String status;
    switch (_avatarState) {
      case 'listening':
        status = _voicePhase == VoicePhase.command ? 'Listening for command...' : 'Listening...';
      case 'thinking':
        status = 'Processing...';
      case 'speaking':
        status = 'Speaking...';
      case 'error':
        status = 'Something went wrong. Try again.';
      default:
        if (_wakeWordMode) {
          status = _voicePhase == VoicePhase.command
              ? 'Command received. Speak...'
              : 'Say "Hey Jarvis" to activate';
        } else {
          status = 'Type a message below to chat';
        }
    }

    return Container(
      padding: Display.padding(context),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: _hud.withValues(alpha: 0.1), width: 0.5)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(status,
              style: TextStyle(
                color: _avatarState == 'speaking' ? _hud : _textDim,
                fontSize: 12,
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis),
          SizedBox(height: 8),
          _buildChatInput(),
        ],
      ),
    );
  }

  Widget _buildChatInput() {
    return Container(
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _hud.withValues(alpha: 0.15), width: 0.5),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _chatController,
              style: TextStyle(color: _text, fontSize: 13),
              decoration: InputDecoration(
                hintText: 'Type message...',
                hintStyle: TextStyle(color: _textDim),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (t) => _sendChat(t),
            ),
          ),
          IconButton(
            icon: Icon(Icons.send, color: _hud, size: 18),
            onPressed: () => _sendChat(_chatController.text),
            padding: EdgeInsets.all(8),
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

class _ChatMessage {
  final String sender;
  final String content;
  final DateTime time;
  final Color color;
  _ChatMessage(this.sender, this.content, this.time, this.color);
}
