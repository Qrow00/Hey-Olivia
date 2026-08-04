import 'package:flutter/material.dart';
import 'dart:math' as math;

class CompactAvatarWidget extends StatefulWidget {
  final String currentState;
  final double size;

  const CompactAvatarWidget({
    super.key,
    required this.currentState,
    this.size = 120,
  });

  @override
  State<CompactAvatarWidget> createState() => _CompactAvatarWidgetState();
}

class _CompactAvatarWidgetState extends State<CompactAvatarWidget>
    with TickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(seconds: 6),
      vsync: this,
    )..repeat();
  }

  @override
  void didUpdateWidget(CompactAvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentState != widget.currentState) {
      _updateSpeed();
    }
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
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return CustomPaint(
          size: Size(widget.size, widget.size),
          painter: _CompactAvatarPainter(
            progress: _controller.value,
            state: widget.currentState,
          ),
        );
      },
    );
  }
}

class _CompactAvatarPainter extends CustomPainter {
  final double progress;
  final String state;

  _CompactAvatarPainter({required this.progress, required this.state});

  Color get _color {
    switch (state) {
      case 'idle': return Color(0xFF00D4FF);
      case 'listening': return Color(0xFF00FF88);
      case 'thinking': return Color(0xFFFFAA00);
      case 'speaking': return Color(0xFF00FFFF);
      case 'error': return Color(0xFFFF4444);
      default: return Color(0xFF00D4FF);
    }
  }

  double get _speed {
    switch (state) {
      case 'idle': return 1.0;
      case 'listening': return 2.5;
      case 'thinking': return 5.0;
      case 'speaking': return 1.5;
      case 'error': return 4.0;
      default: return 1.0;
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final r = size.width / 2 - 4;
    final angle = progress * 2 * math.pi * _speed;

    final bg = Paint()..color = _color.withValues(alpha: 0.08);
    canvas.drawCircle(center, r, bg);

    final outer = Paint()
      ..color = _color.withValues(alpha: 0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawCircle(center, r, outer);

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(angle);
    canvas.translate(-center.dx, -center.dy);

    final arc = Paint()
      ..color = _color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    final arcRadius = r * 0.85;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: arcRadius),
      0, 1.5, false, arc,
    );

    canvas.restore();

    final inner = Paint()
      ..color = _color.withValues(alpha: 0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawCircle(center, r * 0.55, inner);

    final coreGlow = Paint()
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, 12)
      ..color = _color.withValues(alpha: 0.2);
    canvas.drawCircle(center, r * 0.3, coreGlow);

    final core = Paint()..color = _color;
    canvas.drawCircle(center, r * 0.12, core);

    final bright = Paint()
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, 3)
      ..color = Colors.white.withValues(alpha: 0.6);
    canvas.drawCircle(center, r * 0.06, bright);
  }

  @override
  bool shouldRepaint(covariant _CompactAvatarPainter old) =>
      old.progress != progress || old.state != state;
}
