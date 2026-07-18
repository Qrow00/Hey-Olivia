import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/devices_screen.dart';
import 'screens/screen_share_screen.dart';
import 'screens/settings_screen.dart';
import 'services/websocket_service.dart';
import 'services/device_service.dart';
import 'services/screen_share_service.dart';

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

  @override
  void initState() {
    super.initState();
    _deviceService = DeviceService(
      _webSocketService,
      baseUrl: 'http://localhost:8000',
    );
    _screenShareService = ScreenShareService(_webSocketService);
    _connectToServer();
  }

  void _connectToServer() {
    _webSocketService.connect('ws://localhost:8000/ws');
    _deviceService.fetchDevices();
  }

  @override
  void dispose() {
    _webSocketService.dispose();
    _deviceService.dispose();
    _screenShareService.dispose();
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
        items: [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.devices), label: 'Devices'),
          BottomNavigationBarItem(
              icon: Icon(Icons.screen_share), label: 'Screen'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }

  List<Widget> get _screens => [
        HomeScreen(),
        DevicesScreen(deviceService: _deviceService),
        ScreenShareScreen(screenShareService: _screenShareService),
        SettingsScreen(),
      ];
}
