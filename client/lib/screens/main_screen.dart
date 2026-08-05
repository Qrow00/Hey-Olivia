import 'dart:io' show Platform, exit;
import 'package:flutter/material.dart';
import 'home_screen.dart';
import 'health_screen.dart';
import 'devices_screen.dart';
import 'settings_screen.dart';
import 'onboarding_screen.dart';
import 'smart_home_screen.dart';
import 'monitoring_screen.dart';
import 'screen_share_screen.dart';
import 'camera_screen.dart';
import 'personality_screen.dart';
import 'specs_check_screen.dart';
import '../services/websocket_service.dart';
import '../services/voice_service.dart';
import '../services/device_service.dart';
import '../services/screen_share_service.dart';
import '../services/camera_service.dart';
import '../services/wearable_service.dart';
import '../services/smart_home_service.dart';
import '../services/vision_service.dart';
import '../services/server_config.dart';
import '../utils/responsive.dart';
import '../utils/theme.dart';

const _bg = AppTheme.bg;
const _panel = AppTheme.panel;
const _hud = AppTheme.hud;
const _hudDim = AppTheme.hudDim;
const _text = AppTheme.text;
const _textDim = AppTheme.textDim;
const _danger = AppTheme.accentAmber;
const _success = AppTheme.accentGreen;

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => MainScreenState();
}

class MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  bool _servicesReady = false;
  final WebSocketService _webSocketService = WebSocketService();
  late final VoiceService _voiceService;
  late final DeviceService _deviceService;
  late final ScreenShareService _screenShareService;
  late final CameraService _cameraService;
  late final WearableService _wearableService;
  late final SmartHomeService _smartHomeService;
  late final VisionService _visionService;
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  void initState() {
    super.initState();
    _initServices();
  }

  Future<void> _initServices() async {
    final config = await ServerConfig.load();
    final baseUrl = config?.baseUrl ?? 'http://localhost:8000';
    final token = config?.token;

    _deviceService = DeviceService(_webSocketService, baseUrl: baseUrl, token: token);
    _voiceService = VoiceService(_webSocketService);
    _screenShareService = ScreenShareService(_webSocketService);
    _cameraService = CameraService(_webSocketService, baseUrl: baseUrl);
    _wearableService = WearableService(_webSocketService, baseUrl: baseUrl);
    _smartHomeService = SmartHomeService(_webSocketService, baseUrl: baseUrl);
    _visionService = VisionService(_webSocketService);

    final wsUrl = config?.wsUrl ?? 'ws://localhost:8000/ws';
    _webSocketService.connect(wsUrl, token: token);
    _deviceService.fetchDevices();
    _cameraService.fetchCameras();
    _wearableService.fetchDevices();
    _smartHomeService.fetchDevices();
    if (mounted) setState(() => _servicesReady = true);
  }

  @override
  void dispose() {
    _webSocketService.send({'type': 'farewell'});
    _webSocketService.dispose();
    _voiceService.dispose();
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
      key: _scaffoldKey,
      backgroundColor: _bg,
      body: _buildBody(),
      bottomNavigationBar: _buildNav(),
      drawer: _buildDrawer(),
    );
  }

  Widget _buildBody() {
    if (!_servicesReady) {
      return const Center(
        child: CircularProgressIndicator(color: _hud),
      );
    }
    switch (_currentIndex) {
      case 0:
        return HomeScreen(webSocketService: _webSocketService, voiceService: _voiceService);
      case 1:
        return HealthScreen(wearableService: _wearableService);
      case 2:
        return DevicesScreen(deviceService: _deviceService);
      default:
        return HomeScreen(webSocketService: _webSocketService, voiceService: _voiceService);
    }
  }

  Widget _buildNav() {
    return Container(
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: _hud.withValues(alpha: 0.15), width: 0.5)),
      ),
      child: BottomNavigationBar(
        currentIndex: _currentIndex,
          onTap: (index) {
          if (index == 3) {
            _scaffoldKey.currentState?.openDrawer();
          } else {
            setState(() => _currentIndex = index);
          }
        },
        backgroundColor: _panel,
        selectedItemColor: _hud,
        unselectedItemColor: _textDim,
        type: BottomNavigationBarType.fixed,
        selectedFontSize: 11,
        unselectedFontSize: 10,
        elevation: 0,
        items: [
          _navItem(Icons.home_outlined, 'Home', 0),
          _navItem(Icons.favorite_outline, 'Health', 1),
          _navItem(Icons.devices_outlined, 'Devices', 2),
          _navItem(Icons.menu, 'More', 3),
        ],
      ),
    );
  }

  BottomNavigationBarItem _navItem(IconData icon, String label, int index) {
    final selected = _currentIndex == index;
    return BottomNavigationBarItem(
      icon: selected
          ? Container(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: _hud.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _hud.withValues(alpha: 0.3), width: 0.5),
              ),
              child: Icon(icon, size: 20, color: _hud),
            )
          : Icon(icon, size: 20),
      label: label,
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      backgroundColor: _panel,
      width: Display.drawerWidth(context),
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDrawerHeader(),
            Divider(color: _hud.withValues(alpha: 0.2), height: 1),
            Expanded(
              child: ListView(
                padding: EdgeInsets.zero,
                children: [
                  _drawerItem(Icons.home_outlined, 'Smart Home', () {
                    _pushScreen(SmartHomeScreen(smartHomeService: _smartHomeService));
                  }),
                  _drawerItem(Icons.monitor_heart_outlined, 'Monitoring', () {
                    _pushScreen(MonitoringScreen(webSocketService: _webSocketService));
                  }),
                  _drawerItem(Icons.screen_share_outlined, 'Screen Share', () {
                    _pushScreen(ScreenShareScreen(screenShareService: _screenShareService));
                  }),
                  _drawerItem(Icons.visibility_outlined, 'Camera / Vision', () {
                    _pushScreen(CameraScreen(cameraService: _cameraService, visionService: _visionService));
                  }),
                  _drawerItem(Icons.psychology_outlined, 'Personality', () {
                    _pushScreen(PersonalityScreen());
                  }),
                  Divider(color: _hud.withValues(alpha: 0.2), height: 24),
                  _drawerItem(Icons.settings_outlined, 'Settings', () {
                    Navigator.push(context, MaterialPageRoute(
                      builder: (_) => SettingsScreen(),
                    ));
                  }),
                  _drawerItem(Icons.dns_outlined, 'System Info', () {
                    Navigator.push(context, MaterialPageRoute(
                      builder: (_) => SpecsCheckScreen(),
                    ));
                  }),
                  _drawerItem(Icons.wifi_tethering, 'Server Config', () {
                    Navigator.push(context, MaterialPageRoute(
                      builder: (_) => OnboardingScreen(initialStep: 1),
                    ));
                  }),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDrawerHeader() {
    return Container(
      padding: Display.cardPadding(context),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _hud.withValues(alpha: 0.15),
              border: Border.all(color: _hud.withValues(alpha: 0.3), width: 1),
            ),
            child: Icon(Icons.smart_toy, color: _hud, size: 20),
          ),
          SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('J.A.R.V.I.S.', style: TextStyle(color: _hud, fontSize: 16, fontWeight: FontWeight.bold)),
              Text('v2.0.0', style: TextStyle(color: _textDim, fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _drawerItem(IconData icon, String title, VoidCallback onTap) {
    final tablet = Display.isTablet(context);
    return ListTile(
      leading: Icon(icon, color: _textDim, size: tablet ? 24 : 20),
      title: Text(title, style: TextStyle(color: _text, fontSize: tablet ? 16 : 14)),
      trailing: Icon(Icons.chevron_right, color: _textDim, size: tablet ? 22 : 18),
      onTap: onTap,
      dense: !tablet,
    );
  }

  void _pushScreen(Widget screen) {
    Navigator.pop(context);
    Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
  }
}
