import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_app/utils/theme.dart';

void main() {
  test('phaseColor returns a distinct color for every phase', () {
    final colors = {
      'idle': AppTheme.phaseColor('idle'),
      'listening': AppTheme.phaseColor('listening'),
      'thinking': AppTheme.phaseColor('thinking'),
      'speaking': AppTheme.phaseColor('speaking'),
      'error': AppTheme.phaseColor('error'),
    };
    expect(colors.values.toSet().length, 5);
    expect(colors['idle'], AppTheme.hud);
    expect(colors['listening'], AppTheme.accentGreen);
    expect(colors['thinking'], AppTheme.accentAmber);
    expect(colors['speaking'], Colors.white);
    expect(colors['error'], AppTheme.accentRed);
  });
}
