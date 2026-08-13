import 'package:flutter/material.dart';

class AvatarWidget extends StatefulWidget {
  final AvatarState state;
  final double size;
  final Duration transitionDuration;

  const AvatarWidget({
    super.key,
    required this.state,
    this.size = 120,
    this.transitionDuration = const Duration(milliseconds: 300),
  });

  @override
  State<AvatarWidget> createState() => _AvatarWidgetState();
}

class _AvatarWidgetState extends State<AvatarWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(begin: 0.95, end: 1.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    _pulseAnimation = Tween<double>(begin: 0.3, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant AvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Trigger animation on state change
  }

  Color _getStateColor() {
    switch (widget.state) {
      case AvatarState.idle:
        return Colors.deepPurple;
      case AvatarState.listening:
        return Colors.deepPurpleAccent;
      case AvatarState.thinking:
        return Colors.amber;
      case AvatarState.speaking:
        return Colors.cyanAccent;
      case AvatarState.error:
        return Colors.redAccent;
    }
  }

  IconData _getStateIcon() {
    switch (widget.state) {
      case AvatarState.idle:
        return Icons.smart_toy;
      case AvatarState.listening:
        return Icons.mic;
      case AvatarState.thinking:
        return Icons.psychology;
      case AvatarState.speaking:
        return Icons.record_voice_over;
      case AvatarState.error:
        return Icons.error;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getStateColor();
    final icon = _getStateIcon();

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.scale(
          scale: widget.state == AvatarState.speaking
              ? _scaleAnimation.value
              : 1.0,
          child: Container(
            width: widget.size,
            height: widget.size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: [
                  color.withOpacity(0.2),
                  color.withOpacity(0.6),
                ],
              ),
              boxShadow: [
                BoxShadow(
                  color: color.withOpacity(widget.state == AvatarState.speaking
                      ? _pulseAnimation.value * 0.5
                      : 0.3),
                  blurRadius: widget.state == AvatarState.speaking
                      ? 30 * _pulseAnimation.value
                      : 15,
                  spreadRadius: widget.state == AvatarState.speaking
                      ? 5 * _pulseAnimation.value
                      : 0,
                ),
              ],
            ),
            child: Center(
              child: Icon(
                icon,
                color: Colors.white,
                size: widget.size * 0.4,
              ),
            ),
          ),
        );
      },
    );
  }
}

enum AvatarState {
  idle,
  listening,
  thinking,
  speaking,
  error,
}