import 'dart:io';
import 'package:flutter/services.dart';

class MicRecorder {
  static const MethodChannel _method = MethodChannel('mic_recorder');
  static const EventChannel _events = EventChannel('mic_recorder_events');

  static bool get isSupported => Platform.isAndroid;

  Stream<List<int>>? _pcm;

  Stream<List<int>> get pcm {
    _pcm ??= _events.receiveBroadcastStream().cast<List<int>>();
    return _pcm!;
  }

  Future<bool> start() async {
    try {
      final ok = await _method.invokeMethod('start');
      return ok == true;
    } catch (e) {
      print('[Mic] start error: $e');
      return false;
    }
  }

  Future<void> stop() async {
    try {
      await _method.invokeMethod('stop');
    } catch (_) {}
  }
}
