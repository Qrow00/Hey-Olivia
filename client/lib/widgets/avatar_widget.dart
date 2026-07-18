import 'package:flutter/material.dart';
import 'dart:math' as math;

class AvatarWidget extends StatefulWidget {
  final String currentState;

  const AvatarWidget({super.key, required this.currentState});

  @override
  State<AvatarWidget> createState() => _AvatarWidgetState();
}

class _AvatarWidgetState extends State<AvatarWidget>
    with TickerProviderStateMixin {
  late AnimationController _breathingController;
  late AnimationController _pulseController;
  late AnimationController _rotationController;

  @override
  void initState() {
    super.initState();
    _breathingController = AnimationController(
      duration: Duration(seconds: 3),
      vsync: this,
    )..repeat(reverse: true);

    _pulseController = AnimationController(
      duration: Duration(milliseconds: 500),
      vsync: this,
    );

    _rotationController = AnimationController(
      duration: Duration(seconds: 2),
      vsync: this,
    );
  }

  @override
  void didUpdateWidget(AvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentState != widget.currentState) {
      _updateAnimations();
    }
  }

  void _updateAnimations() {
    switch (widget.currentState) {
      case 'idle':
        _breathingController.duration = Duration(seconds: 3);
        _pulseController.stop();
        _rotationController.stop();
        break;
      case 'listening':
        _breathingController.duration = Duration(milliseconds: 800);
        _pulseController.repeat(reverse: true);
        _rotationController.stop();
        break;
      case 'thinking':
        _breathingController.duration = Duration(milliseconds: 500);
        _pulseController.repeat(reverse: true);
        _rotationController.repeat();
        break;
      case 'speaking':
        _breathingController.duration = Duration(milliseconds: 300);
        _pulseController.repeat(reverse: true);
        _rotationController.stop();
        break;
      case 'error':
        _breathingController.stop();
        _pulseController.repeat(reverse: true);
        _rotationController.stop();
        break;
    }
  }

  @override
  void dispose() {
    _breathingController.dispose();
    _pulseController.dispose();
    _rotationController.dispose();
    super.dispose();
  }

  Color get _avatarColor {
    switch (widget.currentState) {
      case 'idle':
        return Color(0xFF00d4ff);
      case 'listening':
        return Color(0xFF00ff88);
      case 'thinking':
        return Color(0xFFffaa00);
      case 'speaking':
        return Color(0xFF00ffff);
      case 'error':
        return Color(0xFFff4444);
      default:
        return Color(0xFF00d4ff);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([
        _breathingController,
        _pulseController,
        _rotationController,
      ]),
      builder: (context, child) {
        final breathingValue = _breathingController.value;
        final pulseValue = _pulseController.value;
        final rotationValue = _rotationController.value;

        double size = 200;
        double glowRadius = 30;
        double spreadRadius = 5;

        switch (widget.currentState) {
          case 'listening':
            size = 200 + (pulseValue * 15);
            glowRadius = 30 + (pulseValue * 20);
            spreadRadius = 5 + (pulseValue * 10);
            break;
          case 'thinking':
            size = 200 + (breathingValue * 20);
            glowRadius = 30 + (breathingValue * 30);
            spreadRadius = 5 + (breathingValue * 15);
            break;
          case 'speaking':
            size = 200 + (breathingValue * 10);
            glowRadius = 30 + (breathingValue * 15);
            spreadRadius = 5 + (breathingValue * 8);
            break;
          case 'error':
            final shake = math.sin(pulseValue * math.pi * 4) * 5;
            size = 200 + shake;
            glowRadius = 30 + (pulseValue * 25);
            spreadRadius = 5 + (pulseValue * 12);
            break;
          default:
            size = 200 + (breathingValue * 10);
            glowRadius = 30 + (breathingValue * 10);
            spreadRadius = 5;
        }

        return Transform.rotate(
          angle: rotationValue * 2 * math.pi,
          child: Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _avatarColor.withValues(alpha: 0.3),
              boxShadow: [
                BoxShadow(
                  color: _avatarColor.withValues(alpha: 0.6),
                  blurRadius: glowRadius,
                  spreadRadius: spreadRadius,
                ),
              ],
            ),
            child: Center(
              child: Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _avatarColor,
                  gradient: RadialGradient(
                    colors: [
                      _avatarColor,
                      _avatarColor.withValues(alpha: 0.7),
                    ],
                  ),
                ),
                child: Icon(
                  _getIcon(),
                  color: Colors.white,
                  size: 50,
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  IconData _getIcon() {
    switch (widget.currentState) {
      case 'listening':
        return Icons.mic;
      case 'thinking':
        return Icons.psychology;
      case 'speaking':
        return Icons.volume_up;
      case 'error':
        return Icons.error_outline;
      default:
        return Icons.mic_none;
    }
  }
}
