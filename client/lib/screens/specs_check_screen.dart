import 'package:flutter/material.dart';
import 'dart:math';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import '../services/system_service.dart';
import 'main_screen.dart';
import '../utils/theme.dart';

const Color _void = AppTheme.bg;
const Color _hud = AppTheme.hud;
const Color _panel = AppTheme.panel;
const Color _text = AppTheme.text;
const Color _textDim = AppTheme.textDim;
const Color _danger = AppTheme.accentRed;
const Color _success = AppTheme.accentGreen;

class SpecsCheckScreen extends StatefulWidget {
  const SpecsCheckScreen({super.key});

  @override
  State<SpecsCheckScreen> createState() => _SpecsCheckScreenState();
}

class _SpecsCheckScreenState extends State<SpecsCheckScreen>
    with TickerProviderStateMixin {
  final SystemService _systemService = SystemService(
    baseUrl: 'http://localhost:8000',
  );

  bool _scanning = true;
  bool _backendOnline = false;
  bool _specsLoaded = false;
  String _scanPhase = 'INITIALIZING';
  Map<String, dynamic>? _specsData;
  String _selectedTier = 'medium';

  late AnimationController _ringController;
  late AnimationController _fadeController;
  late AnimationController _lockController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _ringController = AnimationController(
      vsync: this,
      duration: Duration(seconds: 3),
    )..repeat();
    _fadeController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 600),
    );
    _lockController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 400),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    );
    _initialize();
  }

  @override
  void dispose() {
    _ringController.dispose();
    _fadeController.dispose();
    _lockController.dispose();
    super.dispose();
  }

  Future<void> _initialize() async {
    setState(() => _scanPhase = 'CONNECTING');

    final online = await _systemService.checkBackend();
    if (!online) {
      setState(() {
        _backendOnline = false;
        _scanning = false;
        _scanPhase = 'OFFLINE';
      });
      return;
    }

    setState(() {
      _backendOnline = true;
      _scanPhase = 'SCANNING HARDWARE';
    });

    await Future.delayed(Duration(milliseconds: 800));

    final specs = await _systemService.getSpecs();
    if (specs != null) {
      _ringController.stop();
      await _lockController.forward();

      setState(() {
        _specsData = specs;
        _selectedTier = (specs['recommended_tier'] as String?) ?? 'medium';
        _specsLoaded = true;
        _scanning = false;
        _scanPhase = 'SCAN COMPLETE';
      });
      _fadeController.forward();
    } else {
      setState(() {
        _scanning = false;
        _scanPhase = 'SCAN FAILED';
      });
    }
  }

  void _launchJarvis() async {
    setState(() => _scanPhase = 'APPLYING CONFIG');
    await _systemService.applyTier(_selectedTier);

    final dir = await getApplicationDocumentsDirectory();
    await File('${dir.path}/.jarvis_setup_complete').writeAsString('done');

    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const MainScreen(),
        ),
      );
    }
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
                _buildHeader(),
                Expanded(
                  child: _scanning
                      ? _buildScanningState()
                      : !_backendOnline
                          ? _buildOfflineState()
                          : _specsLoaded
                              ? _buildSpecsView()
                              : _buildErrorState(),
                ),
                if (!_scanning && _backendOnline && _specsLoaded)
                  _buildLaunchBar(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        children: [
          Text(
            'J.A.R.V.I.S.',
            style: TextStyle(
              color: _hud,
              fontSize: 20,
              fontWeight: FontWeight.w600,
              letterSpacing: 4,
              fontFamily: 'monospace',
            ),
          ),
          SizedBox(width: 12),
          Container(
            width: 1,
            height: 20,
            color: _textDim,
          ),
          SizedBox(width: 12),
          Text(
            _scanPhase,
            style: TextStyle(
              color: _textDim,
              fontSize: 11,
              letterSpacing: 2,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScanningState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 200,
            height: 200,
            child: AnimatedBuilder(
              animation: _ringController,
              builder: (context, child) {
                return CustomPaint(
                  painter: _ScanRingPainter(
                    progress: _ringController.value,
                    color: _hud,
                  ),
                );
              },
            ),
          ),
          SizedBox(height: 32),
          Text(
            _scanPhase,
            style: TextStyle(
              color: _hud,
              fontSize: 13,
              letterSpacing: 3,
              fontFamily: 'monospace',
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Detecting hardware configuration',
            style: TextStyle(
              color: _textDim,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOfflineState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.cloud_off, color: _danger, size: 48),
          SizedBox(height: 24),
          Text(
            'BACKEND OFFLINE',
            style: TextStyle(
              color: _danger,
              fontSize: 14,
              letterSpacing: 3,
              fontFamily: 'monospace',
            ),
          ),
          SizedBox(height: 12),
          Text(
            'Cannot reach port 8000',
            style: TextStyle(color: _textDim, fontSize: 13),
          ),
          SizedBox(height: 8),
          Text(
            'Start the backend server, then retry',
            style: TextStyle(color: _textDim, fontSize: 12),
          ),
          SizedBox(height: 32),
          GestureDetector(
            onTap: () {
              setState(() {
                _scanning = true;
                _scanPhase = 'RETRYING';
              });
              _ringController.repeat();
              _initialize();
            },
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: BoxDecoration(
                border: Border.all(color: _hud, width: 1),
              ),
              child: Text(
                'RETRY',
                style: TextStyle(
                  color: _hud,
                  fontSize: 12,
                  letterSpacing: 2,
                  fontFamily: 'monospace',
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.warning_amber, color: Color(0xFFd29922), size: 48),
          SizedBox(height: 24),
          Text(
            _scanPhase,
            style: TextStyle(
              color: Color(0xFFd29922),
              fontSize: 14,
              letterSpacing: 3,
              fontFamily: 'monospace',
            ),
          ),
          SizedBox(height: 32),
          GestureDetector(
            onTap: () {
              setState(() {
                _scanning = true;
                _scanPhase = 'RETRYING';
              });
              _ringController.repeat();
              _initialize();
            },
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: BoxDecoration(
                border: Border.all(color: _hud, width: 1),
              ),
              child: Text(
                'RETRY',
                style: TextStyle(
                  color: _hud,
                  fontSize: 12,
                  letterSpacing: 2,
                  fontFamily: 'monospace',
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSpecsView() {
    final specs = _specsData!['specs'];
    final recommended = _specsData!['recommended_tier'] as String;
    final gpu = specs['gpu'];
    final config = _specsData!['preset'];
    final features = config['features'] as Map<String, dynamic>;
    final models = config['models'] as Map<String, dynamic>;

    return FadeTransition(
      opacity: _fadeAnimation,
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionLabel('HARDWARE'),
            SizedBox(height: 12),
            _buildHudReadout('CPU', '${specs['cpu_count']} cores  ${specs['cpu_freq_ghz']} GHz'),
            _buildHudReadout('RAM', '${specs['ram_gb']} GB  (${specs['ram_available_gb']} GB free)'),
            _buildHudReadout('GPU', gpu['has_gpu']
                ? '${gpu['name']}  ${gpu['vram_gb']} GB'
                : 'NOT DETECTED'),
            _buildHudReadout('OS', '${specs['os']} ${specs['architecture']}'),
            SizedBox(height: 32),
            _buildSectionLabel('PERFORMANCE MODE'),
            SizedBox(height: 12),
            _buildTierSelector(recommended),
            SizedBox(height: 32),
            _buildSectionLabel('ACTIVE SYSTEMS'),
            SizedBox(height: 12),
            ...features.entries.map((e) => _buildSystemStatus(e.key, e.value as bool)),
            Divider(color: _panel, height: 24),
            ...models.entries.where((e) => e.value != null).map((e) =>
                _buildModelLine(e.key, e.value.toString())),
            SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionLabel(String text) {
    return Row(
      children: [
        Container(
          width: 3,
          height: 14,
          color: _hud,
        ),
        SizedBox(width: 8),
        Text(
          text,
          style: TextStyle(
            color: _textDim,
            fontSize: 10,
            letterSpacing: 3,
            fontFamily: 'monospace',
          ),
        ),
      ],
    );
  }

  Widget _buildHudReadout(String label, String value) {
    return Container(
      margin: EdgeInsets.only(bottom: 8),
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: _panel,
        border: Border(
          left: BorderSide(color: _hud.withValues(alpha: 0.3), width: 2),
        ),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 48,
            child: Text(
              label,
              style: TextStyle(
                color: _textDim,
                fontSize: 11,
                letterSpacing: 1,
                fontFamily: 'monospace',
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: _text,
                fontSize: 13,
                fontFamily: 'monospace',
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTierSelector(String recommended) {
    final tiers = [
      ('low', 'LOW', 'Minimal footprint. Fast responses, fewer features.', _danger),
      ('medium', 'BALANCED', 'Balanced performance and capability.', _hud),
      ('high', 'FULL', 'All features. Requires dedicated GPU and 16GB+ RAM.', _success),
    ];

    return Column(
      children: tiers.map((tier) {
        final isSelected = _selectedTier == tier.$1;
        final isRecommended = tier.$1 == recommended;
        final color = tier.$4;

        return GestureDetector(
          onTap: () => setState(() => _selectedTier = tier.$1),
          child: Container(
            margin: EdgeInsets.only(bottom: 8),
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isSelected ? color.withValues(alpha: 0.08) : _panel,
              border: Border.all(
                color: isSelected ? color : _panel,
                width: 1,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 4,
                  height: 40,
                  color: isSelected ? color : _textDim.withValues(alpha: 0.3),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            tier.$2,
                            style: TextStyle(
                              color: isSelected ? color : _text,
                              fontSize: 13,
                              letterSpacing: 2,
                              fontFamily: 'monospace',
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          if (isRecommended) ...[
                            SizedBox(width: 8),
                            Text(
                              'RECOMMENDED',
                              style: TextStyle(
                                color: _textDim,
                                fontSize: 9,
                                letterSpacing: 1,
                                fontFamily: 'monospace',
                              ),
                            ),
                          ],
                        ],
                      ),
                      SizedBox(height: 4),
                      Text(
                        tier.$3,
                        style: TextStyle(color: _textDim, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                if (isSelected)
                  Icon(Icons.arrow_forward_ios, color: color, size: 14),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildSystemStatus(String name, bool enabled) {
    final labels = {
      'browser': 'Hermes Browser',
      'vision': 'Camera Vision',
      'wake_word': 'Wake Word',
      'screen_context': 'Screen Analysis',
      'activity_logger': 'Activity Log',
      'motion_detection': 'Motion Detection',
    };

    return Padding(
      padding: EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: enabled ? _success : _danger,
            ),
          ),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              labels[name] ?? name,
              style: TextStyle(
                color: _textDim,
                fontSize: 12,
                fontFamily: 'monospace',
              ),
            ),
          ),
          Text(
            enabled ? 'ON' : 'OFF',
            style: TextStyle(
              color: enabled ? _success : _danger,
              fontSize: 11,
              letterSpacing: 1,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildModelLine(String role, String model) {
    final labels = {
      'llm': 'LLM',
      'vision': 'VISION',
      'stt': 'STT',
      'embedding': 'EMBED',
    };

    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 56,
            child: Text(
              labels[role] ?? role,
              style: TextStyle(
                color: _textDim,
                fontSize: 10,
                letterSpacing: 1,
                fontFamily: 'monospace',
              ),
            ),
          ),
          Text(
            model,
            style: TextStyle(
              color: _hud,
              fontSize: 12,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLaunchBar() {
    return Container(
      padding: EdgeInsets.all(24),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: _panel)),
      ),
      child: SizedBox(
        width: double.infinity,
        height: 52,
        child: GestureDetector(
          onTap: _launchJarvis,
          child: Container(
            decoration: BoxDecoration(
              color: _hud,
            ),
            child: Center(
              child: Text(
                'INITIALIZE',
                style: TextStyle(
                  color: _void,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 4,
                  fontFamily: 'monospace',
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}


class _ScanRingPainter extends CustomPainter {
  final double progress;
  final Color color;

  _ScanRingPainter({required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 8;

    final bgPaint = Paint()
      ..color = color.withValues(alpha: 0.1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawCircle(center, radius, bgPaint);
    canvas.drawCircle(center, radius - 16, bgPaint);

    final arcPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    final angle = progress * 2 * pi;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      angle,
      pi / 3,
      false,
      arcPaint,
    );

    final innerAngle = -progress * 2 * pi * 1.5;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius - 16),
      innerAngle,
      pi / 4,
      false,
      arcPaint..strokeWidth = 1.5,
    );

    final dotPaint = Paint()..color = color;
    for (int i = 0; i < 8; i++) {
      final a = (i / 8) * 2 * pi + angle * 0.5;
      final dx = center.dx + cos(a) * (radius + 4);
      final dy = center.dy + sin(a) * (radius + 4);
      canvas.drawCircle(Offset(dx, dy), 1.5, dotPaint);
    }

    final crosshairPaint = Paint()
      ..color = color.withValues(alpha: 0.4)
      ..strokeWidth = 0.5;

    canvas.drawLine(
      Offset(center.dx - 20, center.dy),
      Offset(center.dx + 20, center.dy),
      crosshairPaint,
    );
    canvas.drawLine(
      Offset(center.dx, center.dy - 20),
      Offset(center.dx, center.dy + 20),
      crosshairPaint,
    );
  }

  @override
  bool shouldRepaint(_ScanRingPainter old) => old.progress != progress;
}


class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Color(0x0800e5ff)
      ..strokeWidth = 0.5;

    final spacing = 40.0;
    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(_GridPainter old) => false;
}



