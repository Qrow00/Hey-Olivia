import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_app/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const JarvisApp());
    expect(find.text('Home'), findsOneWidget);
  });
}
