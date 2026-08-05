import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_app/widgets/avatar_widget.dart';

void main() {
  for (final state in ['idle', 'listening', 'thinking', 'speaking', 'error']) {
    testWidgets('AvatarWidget renders $state without error', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Center(child: AvatarWidget(currentState: state, wordPulse: true)),
        ),
      );
      await tester.pump(const Duration(milliseconds: 250));
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('AvatarWidget slows down under reduced motion', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: const MediaQueryData(disableAnimations: true),
          child: Center(child: AvatarWidget(currentState: 'idle')),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 250));
    expect(tester.takeException(), isNull);
  });
}
