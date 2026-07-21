import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/home_screen.dart';
import 'screens/devices_screen.dart';
import 'screens/screen_share_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/wearable_screen.dart';
import 'screens/smart_home_screen.dart';
import 'screens/personality_screen.dart';
import 'screens/browser_screen.dart';
import 'services/websocket_service.dart';
import 'services/device_service.dart';
import 'services/screen_share_service.dart';
import 'services/camera_service.dart';
import 'services/wearable_service.dart';
import 'services/smart_home_service.dart';
import 'services/vision_service.dart';
import 'services/browser_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const JarvisApp());
}

class JarvisApp extends StatelessWidget {
  const JarvisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'J.A.R.V.I.S.',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.cyan,
        scaffoldBackgroundColor: Color(0xFF0a0a1a),
      ),
      home: MainScreen(),
    );
  }
}

class MainScreen extends StatefulWidget {
  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  final WebSocketService _webSocketService = WebSocketService();
  late final DeviceService _deviceService;
  late final ScreenShareService _screenShareService;
  late final CameraService _cameraService;
  late final WearableService _wearableService;
  late final SmartHomeService _smartHomeService;
  late final VisionService _visionService;
  late final BrowserService _browserService;
  late final List<Widget> _screens;
  StreamSubscription? _exitSub;

  @override
  void initState() {
    super.initState();
    _deviceService = DeviceService(
      _webSocketService,
      baseUrl: 'http://localhost:8000',
    );
    _screenShareService = ScreenShareService(_webSocketService);
    _cameraService = CameraService(_webSocketService);
    _wearableService = WearableService(_webSocketService);
    _smartHomeService = SmartHomeService(_webSocketService);
    _visionService = VisionService(_webSocketService);
    _browserService = BrowserService(_webSocketService);

    _screens = [
      HomeScreen(webSocketService: _webSocketService),
      DevicesScreen(deviceService: _deviceService),
      ScreenShareScreen(screenShareService: _screenShareService),
      CameraScreen(cameraService: _cameraService, visionService: _visionService),
      WearableScreen(wearableService: _wearableService),
      SmartHomeScreen(smartHomeService: _smartHomeService),
      PersonalityScreen(),
      BrowserScreen(browserService: _browserService),
      SettingsScreen(),
    ];

    _webSocketService.connect('ws://localhost:8000/ws');
    _deviceService.fetchDevices();
    _cameraService.fetchCameras();
    _wearableService.fetchDevices();
    _smartHomeService.fetchDevices();

    _exitSub = _webSocketService.exitApp.listen((_) {
      exit(0);
    });
  }

  @override
  void dispose() {
    _exitSub?.cancel();
    _webSocketService.send({'type': 'farewell'});
    Future.delayed(Duration(seconds: 2), () {
      _webSocketService.dispose();
      exit(0);
    });
    _deviceService.dispose();
    _screenShareService.dispose();
    _cameraService.dispose();
    _wearableService.dispose();
    _smartHomeService.dispose();
    _visionService.dispose();
    _browserService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        backgroundColor: Color(0xFF1a1a2e),
        selectedItemColor: Colors.cyan,
        unselectedItemColor: Colors.white54,
        type: BottomNavigationBarType.fixed,
        selectedFontSize: 10,
        unselectedFontSize: 10,
        items: [
          BottomNavigationBarItem(icon: Icon(Icons.home, size: 20), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.devices, size: 20), label: 'Devices'),
          BottomNavigationBarItem(icon: Icon(Icons.screen_share, size: 20), label: 'Screen'),
          BottomNavigationBarItem(icon: Icon(Icons.visibility, size: 20), label: 'Vision'),
          BottomNavigationBarItem(icon: Icon(Icons.watch, size: 20), label: 'Health'),
          BottomNavigationBarItem(icon: Icon(Icons.home_outlined, size: 20), label: 'Smart'),
          BottomNavigationBarItem(icon: Icon(Icons.psychology, size: 20), label: 'Mind'),
          BottomNavigationBarItem(icon: Icon(Icons.language, size: 20), label: 'Browser'),
          BottomNavigationBarItem(icon: Icon(Icons.settings, size: 20), label: 'Settings'),
        ],
      ),
    );
  }
}
