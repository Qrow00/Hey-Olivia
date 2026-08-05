import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  static const Color bg = Color(0xFF050810);
  static const Color panel = Color(0xFF0A0E1A);
  static const Color panelAlt = Color(0xFF121A2E);
  static const Color hud = Color(0xFF40F9FF);
  static const Color hudDim = Color(0xFF0099CC);
  static const Color hudGlow = Color(0xFF00E5FF);
  static const Color text = Color(0xFFE8F6FF);
  static const Color textDim = Color(0xFF7A8BA8);

  static const Color accentGreen = Color(0xFF00FF88);
  static const Color accentAmber = Color(0xFFFFB300);
  static const Color accentRed = Color(0xFFFF4444);

  static const String dataFont = 'monospace';

  static Color phaseColor(String state) {
    switch (state) {
      case 'listening':
        return accentGreen;
      case 'thinking':
        return accentAmber;
      case 'speaking':
        return Colors.white;
      case 'error':
        return accentRed;
      default:
        return hud;
    }
  }
}
