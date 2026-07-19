import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/devices_screen.dart';
import 'screens/screen_share_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/wearable_screen.dart';
import 'screens/smart_home_screen.dart';
import 'services/websocket_service.dart';
import 'services/device_service.dart';
import 'services/screen_share_service.dart';
import 'services/camera_service.dart';
import 'services/wearable_service.dart';
import 'services/smart_home_service.dart';
import 'services/vision_service.dart';

void main() {
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
  late DeviceService _deviceService;
  late ScreenShareService _screenShareService;
  late CameraService _cameraService;
  late WearableService _wearableService;
  late SmartHomeService _smartHomeService;
  late VisionService _visionService;

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
    _connectToServer();
  }

  void _connectToServer() {
    _webSocketService.connect('ws://localhost:8000/ws');
    _deviceService.fetchDevices();
    _cameraService.fetchCameras();
    _wearableService.fetchDevices();
    _smartHomeService.fetchDevices();
  }

  @override
  void dispose() {
    _webSocketService.dispose();
    _deviceService.dispose();
    _screenShareService.dispose();
    _cameraService.dispose();
    _wearableService.dispose();
    _smartHomeService.dispose();
    _visionService.dispose();
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
          BottomNavigationBarItem(icon: Icon(Icons.settings, size: 20), label: 'Settings'),
        ],
      ),
    );
  }

  List<Widget> get _screens => [
        HomeScreen(),
        DevicesScreen(deviceService: _deviceService),
        ScreenShareScreen(screenShareService: _screenShareService),
        CameraScreen(cameraService: _cameraService, visionService: _visionService),
        WearableScreen(wearableService: _wearableService),
        SmartHomeScreen(smartHomeService: _smartHomeService),
        SettingsScreen(),
      ];
}
