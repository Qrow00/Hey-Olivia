import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import 'overlay_widget.dart';

class OverlayManager {
  static OverlayManager? _instance;
  bool _isOverlay = false;
  OverlayWidget? _overlay;

  static OverlayManager get instance {
    _instance ??= OverlayManager._();
    return _instance!;
  }

  OverlayManager._();

  bool get isOverlay => _isOverlay;

  Future<void> init() async {
    await windowManager.ensureInitialized();
    final options = WindowOptions(
      size: Size(240, 320),
      center: true,
      alwaysOnTop: false,
      titleBarStyle: TitleBarStyle.normal,
    );
    await windowManager.waitUntilReadyToShow(options, () async {
      await windowManager.show();
      await windowManager.focus();
    });
  }

  Future<void> toggleOverlay() async {
    if (_isOverlay) {
      await _exitOverlay();
    } else {
      await _enterOverlay();
    }
  }

  Future<void> _enterOverlay() async {
    _isOverlay = true;
    await windowManager.setSize(Size(240, 320));
    await windowManager.setAlwaysOnTop(true);
    await windowManager.setTitleBarStyle(TitleBarStyle.hidden);
    await windowManager.setResizable(false);
    final pos = await windowManager.getPosition();
    await windowManager.setPosition(Offset(
      pos.dx + 100,
      pos.dy + 100,
    ));
  }

  Future<void> _exitOverlay() async {
    _isOverlay = false;
    await windowManager.setSize(Size(420, 820));
    await windowManager.setAlwaysOnTop(false);
    await windowManager.setTitleBarStyle(TitleBarStyle.normal);
    await windowManager.setResizable(true);
    await windowManager.center();
  }

  Future<void> quit() async {
    await windowManager.close();
  }
}
