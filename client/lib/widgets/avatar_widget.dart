import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../utils/theme.dart';

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
      duration: const Duration(seconds: 8),
      vsync: this,
    )..repeat();
    _updateSpeed();
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
      case 'idle':
        _controller.duration = const Duration(seconds: 8);
        break;
      case 'listening':
        _controller.duration = const Duration(seconds: 3);
        break;
      case 'thinking':
        _controller.duration = const Duration(milliseconds: 600);
        break;
      case 'speaking':
        _controller.duration = const Duration(seconds: 4);
        break;
      case 'error':
        _controller.duration = const Duration(milliseconds: 400);
        break;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduced = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return FittedBox(
          fit: BoxFit.contain,
          child: SizedBox(
            width: 300,
            height: 300,
            child: CustomPaint(
              size: const Size(300, 300),
              painter: JarvisHudPainter(
                progress: _controller.value,
                state: widget.currentState,
                wordPulse: widget.wordPulse,
                slowFactor: reduced ? 0.15 : 1.0,
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
  final double slowFactor;

  JarvisHudPainter({
    required this.progress,
    required this.state,
    this.wordPulse = false,
    this.slowFactor = 1.0,
  });

  static const _r = 150.0;
  static const _cx = 150.0;
  static const _cy = 150.0;
  static const _center = Offset(_cx, _cy);

  Color get _tint => AppTheme.phaseColor(state);

  double get _speed {
    switch (state) {
      case 'idle':
        return 0.4;
      case 'listening':
        return 1.2;
      case 'thinking':
        return 3.0;
      case 'speaking':
        return 0.8;
      case 'error':
        return 2.5;
      default:
        return 0.6;
    }
  }

  String get _phaseLabel {
    switch (state) {
      case 'listening':
        return 'SCANNING';
      case 'thinking':
        return 'PROCESSING';
      case 'speaking':
        return 'VOICE OUTPUT';
      case 'error':
        return 'SYSTEM FAULT';
      default:
        return 'ALL SYSTEMS FUNCTIONING';
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final t = progress * _speed * slowFactor;
    final breathe = 1.0 + 0.012 * math.sin(t * math.pi * 0.5);
    final pulse = wordPulse
        ? 1.0 + 0.28 * (0.5 + 0.5 * math.sin(t * 6 * math.pi))
        : 1.0;

    _drawBgFog(canvas, t);
    _drawCornerBrackets(canvas, t);
    _drawTickRing(canvas, t, breathe);
    _drawSegmentedRings(canvas, t, breathe);
    _drawParticleStreams(canvas, t, breathe);
    _drawCore(canvas, t, pulse);
    _drawReadouts(canvas, t);
    _drawWordmark(canvas, t);
  }

  void _drawBgFog(Canvas canvas, double t) {
    canvas.drawCircle(
      _center, _r,
      Paint()
        ..shader = RadialGradient(
          colors: [_tint.withValues(alpha: 0.05), _tint.withValues(alpha: 0)],
        ).createShader(Rect.fromCircle(center: _center, radius: _r)),
    );
  }

  void _drawCornerBrackets(Canvas canvas, double t) {
    final blink = 0.6 + 0.4 * math.sin(t * 2 * math.pi);
    const positions = [
      [-1.0, -1.0, 0.0],
      [1.0, -1.0, math.pi / 2],
      [1.0, 1.0, math.pi],
      [-1.0, 1.0, -math.pi / 2],
    ];
    final bracketR = _r * 0.95;
    final size = _r * 0.06;
    final gap = _r * 0.015;
    for (final p in positions) {
      canvas.save();
      canvas.translate(_cx + p[0] * bracketR, _cy + p[1] * bracketR);
      canvas.rotate(p[2]);
      final paint = Paint()
        ..color = _tint.withValues(alpha: 0.45 * blink)
        ..strokeWidth = 1.5;
      canvas.drawLine(Offset(-size - gap, -gap), Offset(-gap, -gap), paint);
      canvas.drawLine(Offset(-gap, -gap), Offset(-gap, -size - gap), paint);
      canvas.restore();
    }
  }

  void _drawTickRing(Canvas canvas, double t, double breathe) {
    const count = 40;
    final tickR = _r * 0.92 * breathe;
    final activeOffset = (t * 4).round() % count;
    for (int i = 0; i < count; i++) {
      final a = i * 2 * math.pi / count;
      final lit = ((i - activeOffset) % count) < 5;
      final innerR = tickR * (lit ? 0.94 : 0.96);
      final outerR = tickR * (lit ? 1.0 : 0.99);
      canvas.drawLine(
        Offset(_cx + math.cos(a) * innerR, _cy + math.sin(a) * innerR),
        Offset(_cx + math.cos(a) * outerR, _cy + math.sin(a) * outerR),
        Paint()
          ..color = _tint.withValues(alpha: lit ? 0.7 : 0.12)
          ..strokeWidth = lit ? 1.4 : 0.6,
      );
    }
    canvas.drawLine(
      Offset(_cx, _cy - tickR - 2),
      Offset(_cx, _cy - tickR - 8),
      Paint()
        ..color = _tint.withValues(alpha: 0.8 + 0.2 * math.sin(t * 2 * math.pi))
        ..strokeWidth = 2,
    );
  }

  void _drawSegmentedRings(Canvas canvas, double t, double breathe) {
    final specs = <({double radius, double start, double width, double alpha})>[
      (radius: _r * 0.72, start: t * 0.5, width: 1.4, alpha: 0.35),
      (radius: _r * 0.60, start: -t * 0.7, width: 1.0, alpha: 0.25),
    ];
    for (final s in specs) {
      final rr = s.radius * breathe;
      final paint = Paint()
        ..color = _tint.withValues(alpha: s.alpha)
        ..style = PaintingStyle.stroke
        ..strokeWidth = s.width
        ..strokeCap = StrokeCap.round;
      for (int seg = 0; seg < 3; seg++) {
        final start = s.start + seg * (2 * math.pi / 3);
        canvas.drawArc(
          Rect.fromCircle(center: _center, radius: rr),
          start, 0.45, false, paint,
        );
      }
    }
  }

  void _drawParticleStreams(Canvas canvas, double t, double breathe) {
    final rings = <({double radius, int count, double speed, double alpha})>[
      (radius: _r * 0.80, count: 16, speed: 1.0, alpha: 0.55),
      (radius: _r * 0.52, count: 12, speed: -1.4, alpha: 0.7),
      (radius: _r * 0.33, count: 8, speed: 2.2, alpha: 0.85),
    ];
    for (final ring in rings) {
      final rr = ring.radius * breathe;
      for (int i = 0; i < ring.count; i++) {
        final a = i * 2 * math.pi / ring.count + t * ring.speed;
        final x = _cx + math.cos(a) * rr;
        final y = _cy + math.sin(a) * rr;
        final size = ring.count > 10 ? 1.6 : 2.2;
        canvas.drawCircle(
          Offset(x, y), size * 2.6,
          Paint()..color = _tint.withValues(alpha: ring.alpha * 0.15),
        );
        canvas.drawCircle(
          Offset(x, y), size,
          Paint()..color = _tint.withValues(alpha: ring.alpha),
        );
      }
    }
  }

  void _drawCore(Canvas canvas, double t, double pulse) {
    final p = 0.5 + 0.5 * math.sin(t * 2 * math.pi);
    final coreR = _r * 0.14;

    canvas.drawCircle(
      _center, coreR * 2.6,
      Paint()
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, 18 + p * 8)
        ..shader = RadialGradient(
          colors: [
            _tint.withValues(alpha: 0.35 + p * 0.15),
            _tint.withValues(alpha: 0.05),
            _tint.withValues(alpha: 0),
          ],
        ).createShader(Rect.fromCircle(center: _center, radius: coreR * 2.6)),
    );

    final spoke = Paint()
      ..color = _tint.withValues(alpha: 0.5)
      ..strokeWidth = 1.2
      ..strokeCap = StrokeCap.round;
    for (int i = 0; i < 3; i++) {
      final a = i * 2 * math.pi / 3 + t * 0.05;
      canvas.drawLine(
        Offset(_cx + math.cos(a) * coreR * 0.25, _cy + math.sin(a) * coreR * 0.25),
        Offset(_cx + math.cos(a) * coreR * 0.9, _cy + math.sin(a) * coreR * 0.9),
        spoke,
      );
    }

    canvas.drawCircle(
      _center, coreR,
      Paint()
        ..color = _tint.withValues(alpha: 0.9)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, 3),
    );
    canvas.drawCircle(
      _center, coreR * 0.82,
      Paint()
        ..color = Colors.white.withValues(alpha: 0.8)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2,
    );
    canvas.drawCircle(
      _center, coreR * 0.55 * (1.0 + p * 0.08 * pulse),
      Paint()
        ..shader = RadialGradient(
          colors: [
            Colors.white.withValues(alpha: 1.0),
            _tint.withValues(alpha: 0.9),
            _tint.withValues(alpha: 0.3),
          ],
        ).createShader(Rect.fromCircle(center: _center, radius: coreR)),
    );
  }

  void _drawReadouts(Canvas canvas, double t) {
    final alpha = 0.35 + 0.15 * (0.5 + 0.5 * math.sin(t * math.pi * 1.3));
    final style = TextStyle(
      color: _tint.withValues(alpha: alpha),
      fontSize: 8,
      letterSpacing: 2.5,
      fontFamily: AppTheme.dataFont,
      fontWeight: FontWeight.w300,
    );
    _label(canvas, 'SYS ONLINE', _cx, _cy - _r * 0.46, style);
    _label(canvas, _phaseLabel, _cx, _cy + _r * 0.46, style);
    _label(canvas, 'TGT: ACQ', _cx - _r * 0.62, _cy, style);
    _label(canvas, 'PWR: 100%', _cx + _r * 0.62, _cy, style);
  }

  void _label(Canvas canvas, String text, double x, double y, TextStyle style) {
    final tp = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
    );
    tp.layout();
    tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
  }

  void _drawWordmark(Canvas canvas, double t) {
    final opacity = 0.55 + 0.25 * (0.5 + 0.5 * math.sin(t * math.pi));
    final style = TextStyle(
      color: _tint.withValues(alpha: opacity),
      fontSize: 12,
      letterSpacing: 6,
      fontFamily: AppTheme.dataFont,
      fontWeight: FontWeight.w400,
    );
    final wordY = _cy + _r * 0.78;
    _label(canvas, 'J.A.R.V.I.S.', _cx, wordY, style);
    canvas.drawLine(
      Offset(_cx - _r * 0.2, wordY + 16),
      Offset(_cx + _r * 0.2, wordY + 16),
      Paint()
        ..color = _tint.withValues(alpha: opacity * 0.5)
        ..strokeWidth = 1,
    );
  }

  @override
  bool shouldRepaint(covariant JarvisHudPainter old) =>
      old.progress != progress ||
      old.state != state ||
      old.wordPulse != wordPulse ||
      old.slowFactor != slowFactor;
}
