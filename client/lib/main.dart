import 'package:flutter/material.dart';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'screens/specs_check_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const JarvisApp());
}

class JarvisApp extends StatefulWidget {
  const JarvisApp({super.key});

  @override
  State<JarvisApp> createState() => _JarvisAppState();
}

class _JarvisAppState extends State<JarvisApp> {
  bool _loading = true;
  bool _setupComplete = false;

  @override
  void initState() {
    super.initState();
    _checkSetup();
  }

  Future<void> _checkSetup() async {
    final dir = await getApplicationDocumentsDirectory();
    final flag = File('${dir.path}/.jarvis_setup_complete');
    final exists = await flag.exists();
    setState(() {
      _setupComplete = exists;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData.dark().copyWith(
          scaffoldBackgroundColor: Color(0xFF0a0a1a),
        ),
        home: Scaffold(
          backgroundColor: Color(0xFF0a0a1a),
          body: Center(
            child: CircularProgressIndicator(color: Color(0xFF00e5ff)),
          ),
        ),
      );
    }

    return MaterialApp(
      title: 'J.A.R.V.I.S.',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.cyan,
        scaffoldBackgroundColor: Color(0xFF0a0a1a),
      ),
      home: _setupComplete ? JarvisMainScreen(initialTier: 'auto') : SpecsCheckScreen(),
    );
  }
}
