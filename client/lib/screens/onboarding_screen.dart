import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/server_config.dart';
import 'main_screen.dart';

const _void = Color(0xFF06080d);
const _hud = Color(0xFF00e5ff);
const _panel = Color(0xFF0d1117);
const _text = Color(0xFFc9d1d9);
const _textDim = Color(0xFF6e7681);
const _success = Color(0xFF3fb950);
const _danger = Color(0xFFf85149);

class OnboardingScreen extends StatefulWidget {
  final int initialStep;
  const OnboardingScreen({super.key, this.initialStep = 0});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  late PageController _pageController;
  int _currentStep = 0;
  final _urlController = TextEditingController(text: 'http://localhost:8000');
  bool _testing = false;
  String? _testResult;
  Map<String, dynamic>? _welcomeData;
  bool _saving = false;

  List<Map<String, dynamic>> _profiles = [];
  String? _selectedProfileId;
  String? _authToken;

  final int _stepCount = 4;

  @override
  void initState() {
    super.initState();
    _currentStep = widget.initialStep;
    _pageController = PageController(initialPage: widget.initialStep);
  }

  @override
  void dispose() {
    _pageController.dispose();
    _urlController.dispose();
    super.dispose();
  }

  void _goNext() {
    if (_currentStep < _stepCount - 1) {
      _pageController.nextPage(
        duration: Duration(milliseconds: 400),
        curve: Curves.easeOut,
      );
    }
  }

  Future<void> _testConnection() async {
    setState(() {
      _testing = true;
      _testResult = null;
      _welcomeData = null;
    });

    final ok = await ServerConfig.testConnection(_urlController.text.trim());
    if (!mounted) return;

    if (ok) {
      try {
        final resp = await http
            .get(Uri.parse('${_urlController.text.trim()}/api/v1/system/welcome'))
            .timeout(Duration(seconds: 5));
        if (resp.statusCode == 200) {
          _welcomeData = json.decode(resp.body) as Map<String, dynamic>;
        }
      } catch (_) {}
      setState(() {
        _testResult = 'connected';
        _testing = false;
      });
    } else {
      setState(() {
        _testResult = 'failed';
        _testing = false;
      });
    }
  }

  Future<void> _fetchProfiles() async {
    try {
      final resp = await http
          .get(Uri.parse('${_urlController.text.trim()}/api/v1/auth/profiles'))
          .timeout(Duration(seconds: 5));
      if (resp.statusCode == 200) {
        final data = json.decode(resp.body) as List;
        setState(() => _profiles = data.cast<Map<String, dynamic>>());
      }
    } catch (_) {
      setState(() => _profiles = []);
    }
  }

  Future<bool> _login(String profileId) async {
    try {
      final resp = await http.post(
        Uri.parse('${_urlController.text.trim()}/api/v1/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'profile_id': profileId}),
      ).timeout(Duration(seconds: 5));
      if (resp.statusCode == 200) {
        final data = json.decode(resp.body);
        _authToken = data['token'] as String?;
        return _authToken != null;
      }
    } catch (_) {}
    return false;
  }

  Future<void> _complete() async {
    setState(() => _saving = true);
    final url = _urlController.text.trim();
    final config = ServerConfig(
      baseUrl: url,
      wsUrl: ServerConfig.wsFromBase(url),
      tailscaleIp: _welcomeData?['tailscale']?['ip'] as String?,
      token: _authToken,
      profileId: _selectedProfileId,
      profileName: _profiles.isNotEmpty
          ? (_profiles.firstWhere(
              (p) => p['id'] == _selectedProfileId,
              orElse: () => {'name': 'Default'},
            )['name'] as String?)
          : null,
    );
    await config.save();
    if (!mounted) return;

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => MainScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _void,
      body: Stack(
        children: [
          CustomPaint(
            painter: _GridPainter(),
            size: Size.infinite,
          ),
          SafeArea(
            child: Column(
              children: [
                _buildTopBar(),
                Expanded(
                  child: PageView(
                    controller: _pageController,
                    onPageChanged: (i) => setState(() => _currentStep = i),
                    children: [
                      _buildWelcomeStep(),
                      _buildConnectStep(),
                      _buildProfileStep(),
                      _buildCompleteStep(),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopBar() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        children: [
          Text('J.A.R.V.I.S.',
              style: TextStyle(color: _hud, fontSize: 20, fontWeight: FontWeight.w600,
                  letterSpacing: 4, fontFamily: 'monospace')),
          Spacer(),
          ...List.generate(_stepCount, (i) {
            return Container(
              width: 8, height: 8,
              margin: EdgeInsets.only(left: 8),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: i <= _currentStep ? _hud : _textDim.withValues(alpha: 0.3),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildWelcomeStep() {
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 160, height: 160,
              child: CustomPaint(painter: _AvatarPainter()),
            ),
            SizedBox(height: 32),
            Text('WELCOME',
                style: TextStyle(color: _hud, fontSize: 28, letterSpacing: 6,
                    fontFamily: 'monospace', fontWeight: FontWeight.w700)),
            SizedBox(height: 16),
            Text('Your personal AI assistant\nis ready to be set up.',
                textAlign: TextAlign.center,
                style: TextStyle(color: _textDim, fontSize: 14, height: 1.6)),
            SizedBox(height: 48),
            _buildHudButton('GET STARTED', _goNext),
          ],
        ),
      ),
    );
  }

  Widget _buildConnectStep() {
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('CONNECT TO SERVER',
                style: TextStyle(color: _hud, fontSize: 16, letterSpacing: 3,
                    fontFamily: 'monospace', fontWeight: FontWeight.w600)),
            SizedBox(height: 24),
            Container(
              padding: EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: _panel,
                border: Border.all(color: _textDim.withValues(alpha: 0.3)),
              ),
              child: TextField(
                controller: _urlController,
                style: TextStyle(color: _text, fontFamily: 'monospace', fontSize: 14),
                decoration: InputDecoration(
                  border: InputBorder.none,
                  hintText: 'http://100.x.x.x:8000',
                  hintStyle: TextStyle(color: _textDim.withValues(alpha: 0.5), fontFamily: 'monospace'),
                ),
              ),
            ),
            SizedBox(height: 16),
            _buildHudButton(
              _testing ? 'TESTING...' : 'TEST CONNECTION',
              _testing ? null : _testConnection,
            ),
            if (_testResult != null) ...[
              SizedBox(height: 16),
              _buildConnectionResult(),
            ],
            if (_testResult == 'connected' && _welcomeData != null) ...[
              SizedBox(height: 20),
              _buildServerInfo(),
            ],
            if (_testResult == 'connected') ...[
              SizedBox(height: 24),
              _buildHudButton('NEXT →', () {
                _fetchProfiles();
                _goNext();
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildConnectionResult() {
    final ok = _testResult == 'connected';
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: (ok ? _success : _danger).withValues(alpha: 0.08),
        border: Border(left: BorderSide(color: ok ? _success : _danger, width: 2)),
      ),
      child: Row(
        children: [
          Icon(ok ? Icons.check_circle : Icons.error, color: ok ? _success : _danger, size: 18),
          SizedBox(width: 12),
          Text(ok ? 'Connected successfully' : 'Connection failed',
              style: TextStyle(color: _text, fontSize: 13, fontFamily: 'monospace')),
        ],
      ),
    );
  }

  Widget _buildServerInfo() {
    final ts = _welcomeData!['tailscale'] as Map? ?? {};
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _panel,
        border: Border(left: BorderSide(color: _hud.withValues(alpha: 0.3), width: 2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('SERVER', style: TextStyle(color: _textDim, fontSize: 10, letterSpacing: 2, fontFamily: 'monospace')),
          SizedBox(height: 8),
          Text('v${_welcomeData!['version']}', style: TextStyle(color: _text, fontSize: 12, fontFamily: 'monospace')),
          if (ts['ip'] != null) ...[
            SizedBox(height: 4),
            Text('Tailscale: ${ts['ip']}', style: TextStyle(color: _text, fontSize: 12, fontFamily: 'monospace')),
          ],
        ],
      ),
    );
  }

  Widget _buildProfileStep() {
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('WHO ARE YOU?',
                style: TextStyle(color: _hud, fontSize: 16, letterSpacing: 3,
                    fontFamily: 'monospace', fontWeight: FontWeight.w600)),
            SizedBox(height: 24),
            if (_profiles.isEmpty)
              _buildSingleProfileOption()
            else
              Expanded(
                child: ListView.builder(
                  itemCount: _profiles.length,
                  itemBuilder: (ctx, i) {
                    final p = _profiles[i];
                    final selected = _selectedProfileId == p['id'];
                    return GestureDetector(
                      onTap: () => setState(() => _selectedProfileId = p['id']),
                      child: Container(
                        margin: EdgeInsets.only(bottom: 12),
                        padding: EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: selected ? _hud.withValues(alpha: 0.1) : _panel,
                          border: Border.all(
                            color: selected ? _hud : _textDim.withValues(alpha: 0.2),
                            width: selected ? 1 : 0.5,
                          ),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 40, height: 40,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _hud.withValues(alpha: selected ? 0.2 : 0.08),
                              ),
                              child: Icon(Icons.person, color: _hud, size: 22),
                            ),
                            SizedBox(width: 14),
                            Expanded(
                              child: Text(p['name'] ?? p['id'],
                                  style: TextStyle(color: _text, fontSize: 15,
                                      fontFamily: 'monospace')),
                            ),
                            if (selected)
                              Icon(Icons.check_circle, color: _hud, size: 20),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            if (_selectedProfileId != null) ...[
              SizedBox(height: 16),
              _buildHudButton('CONFIRM', () async {
                final ok = await _login(_selectedProfileId!);
                if (ok && mounted) {
                  _goNext();
                }
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSingleProfileOption() {
    return Column(
      children: [
        Container(
          padding: EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: _panel,
            border: Border.all(color: _textDim.withValues(alpha: 0.2), width: 0.5),
          ),
          child: Column(
            children: [
              Icon(Icons.person_outline, color: _hud, size: 48),
              SizedBox(height: 12),
              Text('Default profile',
                  style: TextStyle(color: _text, fontSize: 14, fontFamily: 'monospace')),
              SizedBox(height: 4),
              Text('No other profiles found',
                  style: TextStyle(color: _textDim, fontSize: 11, fontFamily: 'monospace')),
            ],
          ),
        ),
        SizedBox(height: 20),
        _buildHudButton('CONTINUE AS DEFAULT', () async {
          _selectedProfileId = 'default';
          final ok = await _login('default');
          if (ok && mounted) _goNext();
        }),
      ],
    );
  }

  Widget _buildCompleteStep() {
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle, color: _success, size: 64),
            SizedBox(height: 24),
            Text('READY',
                style: TextStyle(color: _success, fontSize: 24, letterSpacing: 4,
                    fontFamily: 'monospace', fontWeight: FontWeight.w700)),
            SizedBox(height: 16),
            Text('Configuration saved.\nEntering J.A.R.V.I.S.',
                textAlign: TextAlign.center,
                style: TextStyle(color: _textDim, fontSize: 14, height: 1.6)),
            SizedBox(height: 48),
            _buildHudButton(
              _saving ? 'LOADING...' : 'LAUNCH',
              _saving ? null : _complete,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHudButton(String label, VoidCallback? onTap) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          color: _hud,
          child: Center(
            child: Text(label,
                style: TextStyle(color: _void, fontSize: 13, fontWeight: FontWeight.w700,
                    letterSpacing: 3, fontFamily: 'monospace')),
          ),
        ),
      ),
    );
  }
}

class _AvatarPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final r = size.width / 2 - 8;
    final outer = Paint()..color = _hud.withValues(alpha: 0.15)..style = PaintingStyle.stroke..strokeWidth = 1;
    canvas.drawCircle(center, r, outer);
    canvas.drawCircle(center, r - 20, outer);
    final arc = Paint()..color = _hud..style = PaintingStyle.stroke..strokeWidth = 2.5..strokeCap = StrokeCap.round;
    canvas.drawArc(Rect.fromCircle(center: center, radius: r), -0.5, 2.0, false, arc);
    canvas.drawArc(Rect.fromCircle(center: center, radius: r - 20), 2.0, 1.5, false, arc);
    final dot = Paint()..color = _hud;
    canvas.drawCircle(center, 6, dot);
    canvas.drawCircle(center, 3, Paint()..color = _void);
    final glow = Paint()..color = _hud.withValues(alpha: 0.08)..maskFilter = MaskFilter.blur(BlurStyle.normal, 30);
    canvas.drawCircle(center, r * 0.6, glow);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = Color(0x0800e5ff)..strokeWidth = 0.5;
    for (double x = 0; x < size.width; x += 40) canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    for (double y = 0; y < size.height; y += 40) canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
