import 'package:flutter/material.dart';

class AvatarWidget extends StatefulWidget {
  final String currentState;

  const AvatarWidget({super.key, required this.currentState});

  @override
  State<AvatarWidget> createState() => _AvatarWidgetState();
}

class _AvatarWidgetState extends State<AvatarWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(seconds: 3),
      vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color get _avatarColor {
    switch (widget.currentState) {
      case 'listening':
        return Colors.green;
      case 'thinking':
        return Colors.orange;
      case 'speaking':
        return Colors.cyan;
      case 'error':
        return Colors.red;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: 200 + (_controller.value * 10),
          height: 200 + (_controller.value * 10),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _avatarColor.withValues(alpha: 0.3),
            boxShadow: [
              BoxShadow(
                color: _avatarColor.withValues(alpha: 0.5),
                blurRadius: 30 + (_controller.value * 10),
                spreadRadius: 5,
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
              ),
              child: Icon(
                Icons.mic,
                color: Colors.white,
                size: 50,
              ),
            ),
          ),
        );
      },
    );
  }
}
