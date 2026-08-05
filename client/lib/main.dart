import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import 'screens/onboarding_screen.dart';
import 'screens/main_screen.dart';
import 'services/server_config.dart';
import 'utils/theme.dart';

const _bg = AppTheme.bg;
const _hud = AppTheme.hud;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (!kIsWeb && (Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
    await windowManager.ensureInitialized();
    final options = WindowOptions(
      size: Size(420, 820),
      center: true,
      title: 'J.A.R.V.I.S.',
      titleBarStyle: TitleBarStyle.normal,
    );
    await windowManager.waitUntilReadyToShow(options, () async {
      await windowManager.show();
      await windowManager.focus();
    });
  }
  runApp(const JarvisApp());
}

class JarvisApp extends StatefulWidget {
  const JarvisApp({super.key});

  @override
  State<JarvisApp> createState() => _JarvisAppState();
}

class _JarvisAppState extends State<JarvisApp> {
  bool _loading = true;
  bool _hasConfig = false;

  @override
  void initState() {
    super.initState();
    _checkConfig();
  }

  Future<void> _checkConfig() async {
    final config = await ServerConfig.resolve();
    setState(() {
      _hasConfig = config != null;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData.dark().copyWith(
          scaffoldBackgroundColor: _bg,
        ),
        home: Scaffold(
          backgroundColor: _bg,
          body: Center(
            child: CircularProgressIndicator(color: _hud),
          ),
        ),
      );
    }

    return MaterialApp(
      title: 'J.A.R.V.I.S.',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.cyan,
        scaffoldBackgroundColor: _bg,
      ),
      home: _hasConfig
          ? MainScreen()
          : OnboardingScreen(initialStep: 0),
    );
  }
}
