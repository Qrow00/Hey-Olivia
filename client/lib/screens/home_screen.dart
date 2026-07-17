import 'package:flutter/material.dart';
import '../widgets/avatar_widget.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _avatarState = 'idle';
  String _lastMessage = 'Ready to assist you.';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Center(
                child: AvatarWidget(currentState: _avatarState),
              ),
            ),
            Container(
              padding: EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Color(0xFF1a1a2e),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Column(
                children: [
                  Text(
                    _lastMessage,
                    style: TextStyle(color: Colors.white70, fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                  SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildActionButton(Icons.mic, 'Voice', () {}),
                      _buildActionButton(Icons.screen_share, 'Screen', () {}),
                      _buildActionButton(Icons.home, 'Home', () {}),
                      _buildActionButton(Icons.settings, 'Settings', () {}),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton(IconData icon, String label, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.cyan.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(icon, color: Colors.cyan, size: 28),
          ),
          SizedBox(height: 8),
          Text(label, style: TextStyle(color: Colors.white70)),
        ],
      ),
    );
  }
}
