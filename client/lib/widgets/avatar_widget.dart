import 'package:flutter/material.dart';
import 'dart:math' as math;

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
  late AnimationController _popController;
  late Animation<double> _popAnimation;
  double _pulseIntensity = 0.0;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(seconds: 6),
      vsync: this,
    )..repeat();

    _popController = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    _popAnimation = TweenSequence<double>([
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 1.25), weight: 30),
      TweenSequenceItem(tween: Tween(begin: 1.25, end: 0.92), weight: 30),
      TweenSequenceItem(tween: Tween(begin: 0.92, end: 1.05), weight: 20),
      TweenSequenceItem(tween: Tween(begin: 1.05, end: 1.0), weight: 20),
    ]).animate(CurvedAnimation(parent: _popController, curve: Curves.easeOut));
  }

  @override
  void didUpdateWidget(AvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentState != widget.currentState) {
      _updateSpeed();
      _popController.forward(from: 0.0);
    }
    if (widget.wordPulse && !oldWidget.wordPulse) {
      _triggerPulse();
    }
  }

  void _triggerPulse() {
    _pulseIntensity = 1.0;
    Future.doWhile(() async {
      await Future.delayed(Duration(milliseconds: 16));
      _pulseIntensity *= 0.88;
      if (_pulseIntensity < 0.01) {
        _pulseIntensity = 0.0;
        return false;
      }
      return true;
    });
  }

  void _updateSpeed() {
    switch (widget.currentState) {
      case 'idle':
        _controller.duration = Duration(seconds: 6);
      case 'listening':
        _controller.duration = Duration(seconds: 2);
      case 'thinking':
        _controller.duration = Duration(milliseconds: 800);
      case 'speaking':
        _controller.duration = Duration(seconds: 3);
      case 'error':
        _controller.duration = Duration(milliseconds: 300);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _popController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_controller, _popController]),
      builder: (context, _) {
        final scale = _popAnimation.value;
        return Transform.scale(
          scale: scale,
          child: CustomPaint(
            size: Size(300, 300),
            painter: JarvisAvatarPainter(
              progress: _controller.value,
              state: widget.currentState,
              pulseIntensity: _pulseIntensity,
            ),
          ),
        );
      },
    );
  }
}

class JarvisAvatarPainter extends CustomPainter {
  final double progress;
  final String state;
  final double pulseIntensity;

  JarvisAvatarPainter({
    required this.progress,
    required this.state,
    this.pulseIntensity = 0.0,
  });

  Color get _stateColor {
    switch (state) {
      case 'idle':
        return Color(0xFF00D4FF);
      case 'listening':
        return Color(0xFF00FF88);
      case 'thinking':
        return Color(0xFFFFAA00);
      case 'speaking':
        return Color(0xFF00FFFF);
      case 'error':
        return Color(0xFFFF4444);
      default:
        return Color(0xFF00D4FF);
    }
  }

  double _speedMultiplier() {
    switch (state) {
      case 'idle':
        return 1.0;
      case 'listening':
        return 2.5;
      case 'thinking':
        return 5.0;
      case 'speaking':
        return 1.5;
      case 'error':
        return 4.0;
      default:
        return 1.0;
    }
  }

  double _breathe(double offset, double speed, double min, double max) {
    final t = (progress * speed * _speedMultiplier() + offset) % 1.0;
    return min + (max - min) * (0.5 + 0.5 * math.sin(t * 2 * math.pi));
  }

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final baseRadius = size.width / 2;
    final pulseScale = 1.0 + pulseIntensity * 0.12;
    final r = baseRadius * pulseScale;

    final mainAngle = progress * 2 * math.pi * _speedMultiplier();
    final reverseAngle = -mainAngle * 0.8;

    _drawGlow(canvas, center, r);
    _drawOuterRing(canvas, center, r, mainAngle);
    _drawMiddleRing(canvas, center, r, reverseAngle);
    _drawInnerRing(canvas, center, r);
    _drawCoreBg(canvas, center, r);
    _drawCoreReactor(canvas, center, r);
    _drawCoreCenter(canvas, center, r);
    _drawScanLine(canvas, center, r, mainAngle);
    _drawDataPoints(canvas, center, r);
    _drawStatusIndicators(canvas, center, r);
  }

  void _drawGlow(Canvas canvas, Offset center, double radius) {
    final baseOpacity = _breathe(0, 0.15, 0.1, 0.35);
    final opacity = (baseOpacity + pulseIntensity * 0.4).clamp(0.0, 1.0);
    final scale = _breathe(0, 0.15, 1.0, 1.1) + pulseIntensity * 0.08;
    final paint = Paint()
      ..shader = RadialGradient(
        colors: [
          _stateColor.withValues(alpha: opacity),
          _stateColor.withValues(alpha: 0.0),
        ],
      ).createShader(
        Rect.fromCircle(center: center, radius: radius * 1.1 * scale),
      );
    canvas.drawCircle(center, radius * 1.1 * scale, paint);
  }

  void _drawOuterRing(Canvas canvas, Offset center, double radius, double angle) {
    final ringRadius = radius * 0.93;
    final breatheScale = _breathe(0.1, 0.3, 0.97, 1.03) + pulseIntensity * 0.03;
    final opacity = _breathe(0.1, 0.3, 0.5, 0.9);

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.scale(breatheScale);
    canvas.rotate(angle);
    canvas.translate(-center.dx, -center.dy);

    final dashedPaint = Paint()
      ..color = _stateColor.withValues(alpha: opacity)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    _drawDashedCircle(canvas, center, ringRadius, dashedPaint, 40, 6);

    canvas.restore();
  }

  void _drawMiddleRing(Canvas canvas, Offset center, double radius, double angle) {
    final ringRadius = radius * 0.80;
    final breatheScale = _breathe(0.2, 0.4, 0.97, 1.05) + pulseIntensity * 0.04;
    final opacity = _breathe(0.2, 0.4, 0.6, 1.0);

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.scale(breatheScale);
    canvas.rotate(angle);
    canvas.translate(-center.dx, -center.dy);

    final dashedPaint = Paint()
      ..color = _stateColor.withValues(alpha: opacity * 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    _drawDashedCircle(canvas, center, ringRadius, dashedPaint, 30, 8);

    canvas.restore();
  }

  void _drawInnerRing(Canvas canvas, Offset center, double radius) {
    final ringRadius = radius * 0.67;
    final breatheScale = _breathe(0.3, 0.5, 0.98, 1.06) + pulseIntensity * 0.04;
    final opacity = _breathe(0.3, 0.5, 0.3, 0.6);

    final paint = Paint()
      ..color = _stateColor.withValues(alpha: opacity)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.scale(breatheScale);
    canvas.translate(-center.dx, -center.dy);

    canvas.drawCircle(center, ringRadius, paint);

    canvas.restore();
  }

  void _drawCoreBg(Canvas canvas, Offset center, double radius) {
    final coreRadius = radius * 0.53;
    final breatheScale = _breathe(0, 0.3, 0.96, 1.08) + pulseIntensity * 0.05;
    final opacity = _breathe(0, 0.3, 0.03, 0.1);

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.scale(breatheScale);
    canvas.translate(-center.dx, -center.dy);

    final bgPaint = Paint()
      ..color = _stateColor.withValues(alpha: opacity + pulseIntensity * 0.08)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, coreRadius, bgPaint);

    final borderPaint = Paint()
      ..color = _stateColor.withValues(alpha: _breathe(0, 0.3, 0.6, 1.0))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawCircle(center, coreRadius, borderPaint);

    canvas.restore();
  }

  void _drawCoreReactor(Canvas canvas, Offset center, double radius) {
    final reactorRadius = radius * 0.27;
    final breatheScale = _breathe(0.15, 0.4, 0.97, 1.05) + pulseIntensity * 0.06;
    final opacity = _breathe(0.15, 0.4, 0.1, 0.25);

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.scale(breatheScale);
    canvas.translate(-center.dx, -center.dy);

    final bgPaint = Paint()
      ..color = _stateColor.withValues(alpha: opacity + pulseIntensity * 0.15)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, reactorRadius, bgPaint);

    final borderPaint = Paint()
      ..color = _stateColor.withValues(alpha: _breathe(0.15, 0.4, 0.7, 1.0))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawCircle(center, reactorRadius, borderPaint);

    canvas.restore();
  }

  void _drawCoreCenter(Canvas canvas, Offset center, double radius) {
    final coreRadius = radius * 0.1;
    final breatheScale = _breathe(0.4, 0.6, 0.95, 1.1) + pulseIntensity * 0.1;
    final glowIntensity = _breathe(0.4, 0.6, 0.4, 1.0);

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.scale(breatheScale);
    canvas.translate(-center.dx, -center.dy);

    final glowPaint = Paint()
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, 20 * glowIntensity + pulseIntensity * 15)
      ..color = _stateColor.withValues(alpha: glowIntensity * 0.6 + pulseIntensity * 0.3);
    canvas.drawCircle(center, coreRadius * 2 + pulseIntensity * 10, glowPaint);

    final corePaint = Paint()
      ..color = _stateColor
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, coreRadius * (1.0 + pulseIntensity * 0.3), corePaint);

    final brightPaint = Paint()
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, 8)
      ..color = Colors.white.withValues(alpha: glowIntensity * 0.5 + pulseIntensity * 0.3);
    canvas.drawCircle(center, coreRadius * 0.5, brightPaint);

    canvas.restore();
  }

  void _drawScanLine(Canvas canvas, Offset center, double radius, double angle) {
    if (state != 'listening') return;

    final scanRadius = radius * 0.87;
    final paint = Paint()
      ..color = _stateColor.withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: scanRadius),
      angle * 2,
      math.pi * 0.15,
      false,
      paint,
    );

    final trailPaint = Paint()
      ..color = _stateColor.withValues(alpha: 0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: scanRadius),
      angle * 2 + math.pi * 0.15,
      math.pi * 0.3,
      false,
      trailPaint,
    );
  }

  void _drawDataPoints(Canvas canvas, Offset center, double radius) {
    final dotRadius = 4.0;
    final dist = radius * 0.87;
    final baseOpacity = state == 'idle' ? 0.4 : 0.7;

    for (int i = 0; i < 8; i++) {
      final angle = i * math.pi / 4;
      final pointOffset = Offset(
        center.dx + math.cos(angle) * dist,
        center.dy + math.sin(angle) * dist,
      );

      final breathe = _breathe(i * 0.125, _speedMultiplier() * 0.5, 0.3, 1.0);
      final dotScale = 1.0 + pulseIntensity * 0.5;
      final paint = Paint()
        ..color = _stateColor.withValues(alpha: baseOpacity * breathe + pulseIntensity * 0.3)
        ..style = PaintingStyle.fill;

      canvas.drawCircle(pointOffset, dotRadius * (0.5 + breathe * 0.5) * dotScale, paint);
    }
  }

  void _drawStatusIndicators(Canvas canvas, Offset center, double radius) {
    final dist = radius * 0.93;
    final opacity = _breathe(0.5, 0.3, 0.5, 1.0);
    final paint = Paint()
      ..color = _stateColor.withValues(alpha: opacity)
      ..style = PaintingStyle.fill;

    final positions = [
      Offset(center.dx, center.dy - dist),
      Offset(center.dx + dist, center.dy),
      Offset(center.dx, center.dy + dist),
      Offset(center.dx - dist, center.dy),
    ];

    for (final pos in positions) {
      canvas.drawCircle(pos, 5 + pulseIntensity * 3, paint);
    }
  }

  void _drawDashedCircle(Canvas canvas, Offset center, double radius, Paint paint, int dashCount, double dashLength) {
    final circumference = 2 * math.pi * radius;
    final dashAngle = (dashLength / radius);
    final gapAngle = (circumference / dashCount / radius) - dashAngle;

    for (int i = 0; i < dashCount; i++) {
      final startAngle = (i * (dashAngle + gapAngle));
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        dashAngle,
        false,
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant JarvisAvatarPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.state != state ||
        oldDelegate.pulseIntensity != pulseIntensity;
  }
}
