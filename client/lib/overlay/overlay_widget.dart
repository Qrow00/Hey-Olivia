import 'package:flutter/material.dart';
import '../widgets/compact_avatar_widget.dart';
import '../services/server_config.dart';
import '../services/websocket_service.dart';

class OverlayWidget extends StatefulWidget {
  const OverlayWidget({super.key});

  @override
  State<OverlayWidget> createState() => _OverlayWidgetState();
}

class _OverlayWidgetState extends State<OverlayWidget> {
  final WebSocketService _ws = WebSocketService();
  String _avatarState = 'idle';
  bool _connected = false;
  int _heartRate = 0;
  int _spo2 = 0;
  int _steps = 0;
  bool _wakeEnabled = true;
  bool _pressing = false;

  @override
  void initState() {
    super.initState();
    _connect();
  }

  Future<void> _connect() async {
    final config = await ServerConfig.load();
    if (config != null) {
      _ws.messages.listen(_onMessage);
      _ws.connect(config.wsUrl, token: config.token);
      setState(() => _connected = true);
    }
  }

  void _onMessage(Map<String, dynamic> msg) {
    switch (msg['type']) {
      case 'avatar_state':
        setState(() => _avatarState = msg['state'] as String);
      case 'wearable_health_data':
        setState(() {
          if (msg['metric'] == 'heart_rate') _heartRate = (msg['value'] as num).toInt();
          if (msg['metric'] == 'spo2') _spo2 = (msg['value'] as num).toInt();
          if (msg['metric'] == 'steps') _steps = (msg['value'] as num).toInt();
        });
      case 'wake_word_detected':
        setState(() => _avatarState = 'listening');
    }
  }

  void _toggleWake() {
    _wakeEnabled = !_wakeEnabled;
    _ws.send({'type': _wakeEnabled ? 'wake_word_start' : 'wake_word_stop'});
    setState(() {});
  }

  void _startPtt() {
    setState(() => _pressing = true);
    _ws.send({'type': 'voice_start'});
  }

  void _stopPtt() {
    setState(() => _pressing = false);
    _ws.send({'type': 'voice_stop'});
  }

  @override
  void dispose() {
    _ws.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onPanUpdate: (d) {
        if (d.delta.dx != 0 || d.delta.dy != 0) {
          WindowUtils.move(d.delta);
        }
      },
      child: Container(
        width: 220,
        padding: EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Color(0xFF0a0a1a),
          border: Border.all(color: Color(0xFF00e5ff).withValues(alpha: 0.3), width: 1),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildTitleBar(),
            SizedBox(height: 8),
            CompactAvatarWidget(currentState: _avatarState, size: 100),
            SizedBox(height: 8),
            _buildHealthBar(),
            SizedBox(height: 8),
            _buildControls(),
          ],
        ),
      ),
    );
  }

  Widget _buildTitleBar() {
    return Row(
      children: [
        Container(
          width: 6, height: 6,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _connected ? Color(0xFF3fb950) : Color(0xFFf85149),
          ),
        ),
        SizedBox(width: 6),
        Text(
          'J.A.R.V.I.S.',
          style: TextStyle(
            color: Color(0xFF00e5ff),
            fontSize: 10,
            letterSpacing: 2,
            fontFamily: 'monospace',
          ),
        ),
        Spacer(),
        _buildMenuButton(),
      ],
    );
  }

  Widget _buildMenuButton() {
    return PopupMenuButton<String>(
      icon: Icon(Icons.more_vert, color: Color(0xFF6e7681), size: 14),
      color: Color(0xFF0d1117),
      onSelected: (v) {
        if (v == 'main') _exec('open_main');
        if (v == 'settings') _exec('open_settings');
        if (v == 'quit') _exec('quit');
      },
      itemBuilder: (_) => [
        PopupMenuItem(value: 'main', child: Text('Show Main', style: TextStyle(color: Color(0xFFc9d1d9), fontSize: 12))),
        PopupMenuItem(value: 'settings', child: Text('Settings', style: TextStyle(color: Color(0xFFc9d1d9), fontSize: 12))),
        PopupMenuItem(value: 'quit', child: Text('Quit', style: TextStyle(color: Color(0xFFf85149), fontSize: 12))),
      ],
    );
  }

  Widget _buildHealthBar() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: Color(0xFF0d1117),
        border: Border(left: BorderSide(color: Color(0xFF00e5ff).withValues(alpha: 0.3), width: 1)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _healthDot('♥', _heartRate > 0 ? '$_heartRate' : '--', Color(0xFFf85149)),
          _healthDot('O₂', _spo2 > 0 ? '$_spo2%' : '--%', Color(0xFF00e5ff)),
          _healthDot('⚑', _steps > 0 ? '$_steps' : '--', Color(0xFF3fb950)),
        ],
      ),
    );
  }

  Widget _healthDot(String icon, String value, Color color) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(icon, style: TextStyle(color: color, fontSize: 10)),
        SizedBox(height: 2),
        Text(value, style: TextStyle(color: Color(0xFFc9d1d9), fontSize: 10, fontFamily: 'monospace')),
      ],
    );
  }

  Widget _buildControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        GestureDetector(
          onTap: _toggleWake,
          child: Container(
            padding: EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: _wakeEnabled
                  ? Color(0xFF00e5ff).withValues(alpha: 0.15)
                  : Color(0xFFf85149).withValues(alpha: 0.15),
            ),
            child: Icon(
              _wakeEnabled ? Icons.wifi : Icons.wifi_off,
              color: _wakeEnabled ? Color(0xFF00e5ff) : Color(0xFFf85149),
              size: 16,
            ),
          ),
        ),
        SizedBox(width: 8),
        GestureDetector(
          onTapDown: (_) => _startPtt(),
          onTapUp: (_) => _stopPtt(),
          onTapCancel: _stopPtt,
          child: Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: _pressing ? Color(0xFF00e5ff) : Color(0xFF0d1117),
              border: Border.all(color: Color(0xFF00e5ff).withValues(alpha: 0.5)),
            ),
            child: Icon(
              Icons.mic,
              color: _pressing ? Color(0xFF0a0a1a) : Color(0xFF00e5ff),
              size: 18,
            ),
          ),
        ),
      ],
    );
  }

  void _exec(String action) {
    _ws.send({'type': 'overlay_action', 'action': action});
  }
}

class WindowUtils {
  static Offset _position = Offset.zero;

  static void move(Offset delta) {
    _position = _position + delta;
  }
}
