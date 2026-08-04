import 'dart:math' as math;
import 'package:flutter/material.dart';

class AvatarWidget extends StatefulWidget {
  final String currentState;
  final bool wordPulse;

  const AvatarWidget({super.key, required this.currentState, this.wordPulse = false});

  @override
  State<AvatarWidget> createState() => _AvatarWidgetState();
}

class _AvatarWidgetState extends State<AvatarWidget>
    with TickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(seconds: 8),
      vsync: this,
    )..repeat();
  }

  @override
  void didUpdateWidget(AvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentState != widget.currentState) {
      _updateSpeed();
    }
  }

  void _updateSpeed() {
    switch (widget.currentState) {
      case 'idle': _controller.duration = Duration(seconds: 8); break;
      case 'listening': _controller.duration = Duration(seconds: 3); break;
      case 'thinking': _controller.duration = Duration(milliseconds: 600); break;
      case 'speaking': _controller.duration = Duration(seconds: 4); break;
      case 'error': _controller.duration = Duration(milliseconds: 400); break;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return FittedBox(
          fit: BoxFit.contain,
          child: SizedBox(
            width: 300,
            height: 300,
            child: CustomPaint(
              size: Size(300, 300),
              painter: JarvisHudPainter(
                progress: _controller.value,
                state: widget.currentState,
                wordPulse: widget.wordPulse,
              ),
            ),
          ),
        );
      },
    );
  }
}

class JarvisHudPainter extends CustomPainter {
  final double progress;
  final String state;
  final bool wordPulse;

  JarvisHudPainter({
    required this.progress,
    required this.state,
    this.wordPulse = false,
  });

  static const _primary = Color(0xFF40F9FF);
  static const _secondary = Color(0xFF00B8FF);
  static const _r = 150.0;
  static const _cx = 150.0, _cy = 150.0;
  static const _center = Offset(_cx, _cy);

  Color get _tint {
    switch (state) {
      case 'listening': return const Color(0xFF00FF88);
      case 'thinking': return const Color(0xFFFFAA00);
      case 'speaking': return _primary;
      case 'error': return const Color(0xFFFF4444);
      default: return _primary;
    }
  }

  double _speed() {
    switch (state) {
      case 'idle': return 0.4;
      case 'listening': return 1.2;
      case 'thinking': return 3.0;
      case 'speaking': return 0.8;
      case 'error': return 2.5;
      default: return 0.6;
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final t = progress * _speed();
    final breathe = 1.0 + 0.01 * math.sin(t * math.pi * 0.5);
    final pulse = wordPulse ? 1.0 + 0.3 * (0.5 + 0.5 * math.sin(t * 6 * math.pi)) : 1.0;

    _drawBgFog(canvas, t);
    _drawReticle(canvas, t, breathe, pulse);
    _drawTickMarks(canvas, t, breathe, pulse);
    _drawCrosshairs(canvas, t, breathe);
    _drawBrackets(canvas, t, breathe);
    _drawSweep(canvas, t, breathe);
    _drawDataLabels(canvas, t);
    _drawCore(canvas, t, pulse);
    _drawLabel(canvas, t);
  }

  void _drawBgFog(Canvas canvas, double t) {
    canvas.drawCircle(
      _center, _r,
      Paint()..shader = RadialGradient(
        colors: [_tint.withValues(alpha: 0.025), _tint.withValues(alpha: 0)],
      ).createShader(Rect.fromCircle(center: _center, radius: _r)),
    );
  }

  void _drawReticle(Canvas canvas, double t, double breathe, double pulse) {
    for (int i = 0; i < 3; i++) {
      final rr = _r * (0.36 + i * 0.17) * breathe;
      final alpha = 0.08 + (i == 1 ? 0.10 : 0.0) + pulse * 0.04;
      canvas.drawCircle(
        _center, rr,
        Paint()
          ..color = _primary.withValues(alpha: alpha)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 0.5,
      );
    }
  }

  void _drawTickMarks(Canvas canvas, double t, double breathe, double pulse) {
    final count = 16;
    final tickR = _r * 0.70 * breathe;
    final activeOffset = (t * count).round();

    for (int i = 0; i < count; i++) {
      final a = i * 2 * math.pi / count;
      final isActive = (i + activeOffset) % count < 4;
      final innerR = tickR * (isActive ? 0.92 : 0.94);
      final outerR = tickR * (isActive ? 1.0 : 0.98);
      final alpha = (isActive ? 0.6 : 0.10) + pulse * 0.10;

      canvas.drawLine(
        Offset(_cx + math.cos(a) * innerR, _cy + math.sin(a) * innerR),
        Offset(_cx + math.cos(a) * outerR, _cy + math.sin(a) * outerR),
        Paint()
          ..color = _primary.withValues(alpha: alpha)
          ..strokeWidth = isActive ? 1.2 : 0.5,
      );
    }
  }

  void _drawCrosshairs(Canvas canvas, double t, double breathe) {
    final cr = _r * 0.36 * breathe;
    final len = _r * 0.08;

    for (int i = 0; i < 4; i++) {
      final a = i * math.pi / 2;
      final dx = math.cos(a), dy = math.sin(a);
      final blink = 0.7 + 0.3 * math.sin(t * 3 * math.pi + i * 1.5);

      canvas.drawLine(
        Offset(_cx + dx * (cr - len), _cy + dy * (cr - len)),
        Offset(_cx + dx * cr, _cy + dy * cr),
        Paint()
          ..color = _primary.withValues(alpha: 0.5 * blink)
          ..strokeWidth = 1.5
          ..strokeCap = StrokeCap.round,
      );

      canvas.drawLine(
        Offset(_cx + dx * (_r * breathe * 0.70), _cy + dy * (_r * breathe * 0.70)),
        Offset(_cx + dx * (_r * breathe * 0.70 + len), _cy + dy * (_r * breathe * 0.70 + len)),
        Paint()
          ..color = _primary.withValues(alpha: 0.3 * blink)
          ..strokeWidth = 1.0
          ..strokeCap = StrokeCap.round,
      );
    }
  }

  void _drawBrackets(Canvas canvas, double t, double breathe) {
    final br = _r * 0.78 * breathe;
    final size = _r * 0.06;
    final gap = _r * 0.02;
    final blink = 0.6 + 0.4 * math.sin(t * 2 * math.pi);

    final positions = [
      [-1, -1, 0, 0],
      [1, -1, math.pi / 2, 0],
      [1, 1, math.pi, 0],
      [-1, 1, -math.pi / 2, 0],
    ];

    for (final p in positions) {
      canvas.save();
      canvas.translate(_cx + p[0] * br, _cy + p[1] * br);
      canvas.rotate(p[2] as double);

      final bracketPaint = Paint()
        ..color = _primary.withValues(alpha: 0.3 * blink)
        ..strokeWidth = 1.0;

      canvas.drawLine(Offset(-size - gap, -gap), Offset(-gap, -gap), bracketPaint);
      canvas.drawLine(Offset(-gap, -gap), Offset(-gap, -size - gap), bracketPaint);

      canvas.restore();
    }
  }

  void _drawSweep(Canvas canvas, double t, double breathe) {
    final sr = _r * 0.53 * breathe;
    final angle = t * 2 * math.pi;

    final sweepPaint = Paint()
      ..shader = SweepGradient(
        startAngle: angle - 0.08,
        endAngle: angle + 0.08,
        colors: [
          _primary.withValues(alpha: 0),
          _primary.withValues(alpha: 0.10),
          _primary.withValues(alpha: 0),
        ],
      ).createShader(Rect.fromCircle(center: _center, radius: sr))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    canvas.drawArc(Rect.fromCircle(center: _center, radius: sr), angle - 0.5, 1.0, false, sweepPaint);

    final sweepLine = Paint()
      ..color = _primary.withValues(alpha: 0.2)
      ..strokeWidth = 0.5;
    canvas.drawLine(
      _center,
      Offset(_cx + math.cos(angle) * sr, _cy + math.sin(angle) * sr),
      sweepLine,
    );
  }

  void _drawDataLabels(Canvas canvas, double t) {
    final alpha = 0.2 + 0.1 * (0.5 + 0.5 * math.sin(t * math.pi * 1.3));
    final style = TextStyle(
      color: _primary.withValues(alpha: alpha),
      fontSize: 8,
      letterSpacing: 2,
      fontWeight: FontWeight.w300,
    );

    _drawLabelText(canvas, 'SYS ONLINE', _cx, _cy - _r * 0.48, style);
    _drawLabelText(canvas, 'TARGET ACQ', _cx, _cy + _r * 0.48, style);
    _drawLabelText(canvas, '01', _cx - _r * 0.45, _cy, style);
    _drawLabelText(canvas, '02', _cx + _r * 0.45, _cy, style);
  }

  void _drawLabelText(Canvas canvas, String text, double x, double y, TextStyle style) {
    final tp = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
    );
    tp.layout();
    tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
  }

  void _drawCore(Canvas canvas, double t, double pulse) {
    final coreR = _r * 0.08;
    final p = 0.5 + 0.5 * math.sin(t * 2 * math.pi);

    canvas.save();
    final s = 1.0 + p * 0.02 * pulse;
    canvas.translate(_cx, _cy);
    canvas.scale(s);
    canvas.translate(-_cx, -_cy);

    final glow = Paint()
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, 20 + p * 10)
      ..shader = RadialGradient(
        colors: [
          _tint.withValues(alpha: 0.3 + p * 0.2),
          _secondary.withValues(alpha: 0.08),
          _tint.withValues(alpha: 0),
        ],
      ).createShader(Rect.fromCircle(center: _center, radius: coreR * 3));
    canvas.drawCircle(_center, coreR * 3, glow);

    final core = Paint()
      ..shader = RadialGradient(
        colors: [
          Colors.white.withValues(alpha: 1.0),
          Colors.white.withValues(alpha: 0.95),
          _primary.withValues(alpha: 0.8),
          _secondary.withValues(alpha: 0.2),
        ],
      ).createShader(Rect.fromCircle(center: _center, radius: coreR));
    canvas.drawCircle(_center, coreR, core);

    final hl = Paint()
      ..color = Colors.white.withValues(alpha: 0.8 + p * 0.2);
    canvas.drawCircle(Offset(_cx - coreR * 0.2, _cy - coreR * 0.2), coreR * 0.2, hl);

    canvas.restore();
  }

  void _drawLabel(Canvas canvas, double t) {
    final opacity = 0.20 + 0.10 * (0.5 + 0.5 * math.sin(t * math.pi));

    final tp = TextPainter(
      text: TextSpan(
        text: 'J.A.R.V.I.S.',
        style: TextStyle(
          color: _primary.withValues(alpha: opacity),
          fontSize: 11,
          letterSpacing: 5,
          fontWeight: FontWeight.w200,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    tp.layout();
    tp.paint(canvas, Offset(_cx - tp.width / 2, _cy + _r * 0.58));

    final lineY = _cy + _r * 0.58 + tp.height + 4;
    final lineW = _r * 0.16;
    canvas.drawLine(
      Offset(_cx - lineW, lineY),
      Offset(_cx + lineW, lineY),
      Paint()
        ..color = _primary.withValues(alpha: opacity * 0.4)
        ..strokeWidth = 0.5,
    );
  }

  @override
  bool shouldRepaint(covariant JarvisHudPainter old) =>
      old.progress != progress || old.state != state || old.wordPulse != wordPulse;
}
