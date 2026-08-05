# Reactive Waveform JARVIS Avatar — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the JARVIS avatar as a radial equalizer (44 bars driven by real mic RMS while listening, procedural otherwise) and add a tilt-follow motion parallax using the Android accelerometer.

**Architecture:** A new `MotionSensorPlugin.kt` native Android plugin streams normalized gravity tilt over an EventChannel. `MotionService` (Dart) wraps it and degrades to a zero stream on desktop. `voice_service.dart` computes smoothed mic RMS from the PCM frames it already forwards. `JarvisHudPainter` gains `bars`, `tiltX`, `tiltY` and draws the equalizer + per-depth parallax; `AvatarWidget` accepts optional `micLevel`/`tilt` streams. Home screen wires them in.

**Tech Stack:** Flutter / Dart, Kotlin Android plugin (SensorManager), `CustomPainter`, `EventChannel`, existing dev deps (`flutter_test`, `flutter_lints`). No new dependencies.

## Global Constraints

- No new dependencies — stdlib/Flutter/Android SDK only (Ponytail rung 3/4).
- `AvatarWidget` constructor stays compatible: existing callers pass `currentState` + `wordPulse`; new params are optional and default off.
- `JarvisHudPainter` keeps `progress/state/wordPulse/slowFactor`; adds `bars`, `tiltX`, `tiltY`.
- Phase colors/speeds fixed: idle `#40F9FF` 8s, listening `#00FF88` 3s, thinking `#FFB300` 600ms, speaking white 4s, error `#FF4444` 400ms.
- Reduced motion: `disableAnimations` → `slowFactor` 0.15 (unchanged).
- Parallax is Android-only; Windows desktop keeps current static rendering.
- Channel names: method `motion_sensor`, event `motion_sensor_events`.
- Flutter is NOT on PATH — run via `C:\flutter\bin\flutter.bat`.
- Spec: `docs/superpowers/specs/2026-08-05-jarvis-reactive-avatar-design.md`

---

### Task 1: Android motion sensor plugin

**Files:**
- Create: `client/android/app/src/main/kotlin/com/jarvis/jarvis_app/MotionSensorPlugin.kt`
- Modify: `client/android/app/src/main/kotlin/com/jarvis/jarvis_app/MainActivity.kt`

**Interfaces:**
- Consumes: nothing.
- Produces: Method channel `motion_sensor` with methods `start`/`stop`; Event channel `motion_sensor_events` emitting `DoubleArray` `[tx, ty]` in `[-1, 1]` at ~30 Hz, low-pass filtered gravity tilt. Task 2's `MotionService` consumes these.

- [ ] **Step 1: Create `MotionSensorPlugin.kt`**

```kotlin
package com.jarvis.jarvis_app

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Handler
import android.os.Looper
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class MotionSensorPlugin(
    private val context: Context,
) : MethodChannel.MethodCallHandler, EventChannel.StreamHandler, SensorEventListener {

    companion object {
        private const val ALPHA = 0.1f
        private const val EMIT_INTERVAL_MS = 33L
    }

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    private val handler = Handler(Looper.getMainLooper())

    private var sink: EventChannel.EventSink? = null
    private var registered = false
    private val gravity = FloatArray(3)
    private var lastEmit = 0L

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "start" -> {
                if (accelerometer == null) {
                    result.error("NO_SENSOR", "No accelerometer found", null)
                } else {
                    if (!registered) {
                        registered = true
                        sensorManager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_GAME)
                    }
                    result.success(true)
                }
            }
            "stop" -> {
                unregister()
                result.success(true)
            }
            else -> result.notImplemented()
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        gravity[0] = gravity[0] * ALPHA + event.values[0] * (1 - ALPHA)
        gravity[1] = gravity[1] * ALPHA + event.values[1] * (1 - ALPHA)
        gravity[2] = gravity[2] * ALPHA + event.values[2] * (1 - ALPHA)

        val now = System.currentTimeMillis()
        if (now - lastEmit < EMIT_INTERVAL_MS) return
        lastEmit = now

        val tx = ((gravity[0] - SensorManager.GRAVITY_EARTH) / SensorManager.GRAVITY_EARTH)
            .coerceIn(-1f, 1f)
        val ty = ((gravity[1] - SensorManager.GRAVITY_EARTH) / SensorManager.GRAVITY_EARTH)
            .coerceIn(-1f, 1f)
        handler.post { sink?.success(doubleArrayOf(tx.toDouble(), ty.toDouble())) }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        sink = events
    }

    override fun onCancel(arguments: Any?) {
        sink = null
        unregister()
    }

    private fun unregister() {
        if (registered) {
            registered = false
            sensorManager.unregisterListener(this)
        }
    }
}
```

- [ ] **Step 2: Register the plugin in `MainActivity.kt`**

Add a private field next to the existing ones (line ~24, after `micRecorderPlugin`):

```kotlin
private var motionSensorPlugin: MotionSensorPlugin? = null
```

Add this block at the end of `configureFlutterEngine`, after the `MIC_RECORDER_EVENTS` EventChannel setup (after line 95):

```kotlin
motionSensorPlugin = MotionSensorPlugin(this)
MethodChannel(
    flutterEngine.dartExecutor.binaryMessenger,
    "motion_sensor"
).setMethodCallHandler { call, result ->
    motionSensorPlugin?.onMethodCall(call, result)
}
EventChannel(
    flutterEngine.dartExecutor.binaryMessenger,
    "motion_sensor_events"
).setStreamHandler(motionSensorPlugin)
```

- [ ] **Step 3: Verify the app still builds**

Run: `C:\flutter\bin\flutter.bat build apk --debug`
Expected: BUILD SUCCESSFUL (or no new Kotlin compile errors; existing build state unchanged).

- [ ] **Step 4: Commit**

```bash
git add client/android/app/src/main/kotlin/com/jarvis/jarvis_app/MotionSensorPlugin.kt client/android/app/src/main/kotlin/com/jarvis/jarvis_app/MainActivity.kt
git commit -m "feat(motion): Android accelerometer tilt plugin"
```

---

### Task 2: Dart motion service

**Files:**
- Create: `client/lib/services/motion_service.dart`
- Test: `client/test/motion_service_test.dart`

**Interfaces:**
- Consumes: `motion_sensor` / `motion_sensor_events` channels (Task 1).
- Produces: `MotionService` — `MotionService({bool? supported})`, `Stream<Offset> get tilt`, `Future<bool> start()`, `Future<void> stop()`. Task 4/5 consume `tilt` and `start()/stop()`.

- [ ] **Step 1: Write the failing test**

```dart
import 'dart:typed_data';
import 'dart:ui' show Offset;

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_app/services/motion_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('unsupported platform emits a static zero tilt', () async {
    final svc = MotionService(supported: false);
    expect(await svc.tilt.first, Offset.zero);
  });

  testWidgets('maps and filters tilt events', (tester) async {
    const events = EventChannel('motion_sensor_events');
    tester.binding.defaultBinaryMessenger.setMockStreamHandler(
      events,
      MockStreamHandler.inline(
        onListen: (arguments, sink) {
          sink!.success(Float64List.fromList([0.5, -0.3]));
          sink.success(Float64List.fromList([0.5, -0.3]));
          sink.success(Float64List.fromList([0.6, -0.3]));
        },
        onCancel: (arguments) {},
      ),
    );

    final svc = MotionService(supported: true);
    final offsets = <Offset>[];
    final sub = svc.tilt.listen(offsets.add);
    await tester.pump();
    await Future<void>.delayed(Duration.zero);
    await tester.pump();

    expect(offsets.length, 2, reason: 'duplicate within 0.01 must be filtered');
    expect(offsets[0], const Offset(0.5, -0.3));
    expect(offsets[1], const Offset(0.6, -0.3));

    await svc.stop();
    sub.cancel();
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\flutter\bin\flutter.bat test test/motion_service_test.dart`
Expected: FAIL — `Undefined class 'MotionService'`.

- [ ] **Step 3: Write minimal implementation**

```dart
import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' show Offset;

import 'package:flutter/services.dart';

class MotionService {
  static const MethodChannel _method = MethodChannel('motion_sensor');
  static const EventChannel _events = EventChannel('motion_sensor_events');

  final bool _supported;
  StreamController<Offset>? _tiltController;
  StreamSubscription<Float64List>? _sub;
  Offset _last = Offset.zero;

  MotionService({bool? supported})
      : _supported = supported ?? Platform.isAndroid;

  bool get isSupported => _supported;

  Stream<Offset> get tilt {
    if (!_supported) return Stream<Offset>.value(Offset.zero);
    _tiltController ??= StreamController<Offset>.broadcast();
    _sub ??= _events.receiveBroadcastStream().cast<Float64List>().listen((v) {
      if (v.length < 2) return;
      final offset = Offset(
        v[0].clamp(-1.0, 1.0),
        v[1].clamp(-1.0, 1.0),
      );
      if ((offset - _last).distance > 0.01) {
        _last = offset;
        _tiltController!.add(offset);
      }
    });
    return _tiltController!.stream;
  }

  Future<bool> start() async {
    if (!_supported) return true;
    try {
      final ok = await _method.invokeMethod<bool>('start');
      return ok ?? false;
    } catch (e) {
      print('[Motion] start error: $e');
      return false;
    }
  }

  Future<void> stop() async {
    try {
      await _method.invokeMethod('stop');
    } catch (_) {}
    await _sub?.cancel();
    _sub = null;
    _tiltController?.close();
    _tiltController = null;
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\flutter\bin\flutter.bat test test/motion_service_test.dart`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add client/lib/services/motion_service.dart client/test/motion_service_test.dart
git commit -m "feat(motion): Dart tilt stream wrapper with desktop fallback"
```

---

### Task 3: Mic RMS in voice service

**Files:**
- Modify: `client/lib/services/voice_service.dart`
- Test: `client/test/voice_service_rms_test.dart`

**Interfaces:**
- Consumes: nothing (pure addition to existing service).
- Produces: `static double VoiceService.rms(List<int> pcmBytes)` and `Stream<double> get micLevel` (broadcast, smoothed 0–1). Task 4 consumes `micLevel`.

- [ ] **Step 1: Write the failing test**

```dart
import 'dart:math' as math;

import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_app/services/voice_service.dart';

void main() {
  test('rms of silence is 0', () {
    final pcm = List<int>.filled(320, 0);
    expect(VoiceService.rms(pcm), 0.0);
  });

  test('rms of full-scale square wave is 1', () {
    final pcm = <int>[];
    for (var i = 0; i < 160; i++) {
      pcm.addAll([0x00, 0x80]);
    }
    expect(VoiceService.rms(pcm), closeTo(1.0, 0.001));
  });

  test('rms of known samples', () {
    final pcm = <int>[];
    for (var i = 0; i < 100; i++) {
      pcm.addAll([0x00, 0x40]);
    }
    expect(VoiceService.rms(pcm), closeTo(0.5, 0.001));
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\flutter\bin\flutter.bat test test/voice_service_rms_test.dart`
Expected: FAIL — `Class 'VoiceService' has no instance member 'rms'` (no such static).

- [ ] **Step 3: Implement the static helper**

Add `import 'dart:math' as math;` at the top of `voice_service.dart`. Add this static method to `VoiceService` (place near the class top, after the static getters):

```dart
static double rms(List<int> pcmBytes) {
  if (pcmBytes.length < 2) return 0.0;
  var sum = 0.0;
  for (var i = 0; i + 1 < pcmBytes.length; i += 2) {
    final raw = pcmBytes[i] | (pcmBytes[i + 1] << 8);
    final sample = raw >= 0x8000 ? raw - 0x10000 : raw;
    sum += sample * sample;
  }
  final n = pcmBytes.length ~/ 2;
  return (math.sqrt(sum / n) / 32768.0).clamp(0.0, 1.0);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\flutter\bin\flutter.bat test test/voice_service_rms_test.dart`
Expected: PASS.

- [ ] **Step 5: Add the micLevel stream**

Add fields next to the existing controllers (near line 26, after `_phaseController`):

```dart
final _micLevelController = StreamController<double>.broadcast();
double _smoothedMicLevel = 0.0;
```

Add getter next to the other getters (near line 50):

```dart
Stream<double> get micLevel => _micLevelController.stream;
```

In `_processAudioStream` (currently at line ~425), compute RMS on each chunk before forwarding:

```dart
void _processAudioStream(Stream<List<int>> audioStream) {
  _audioStreamSub?.cancel();
  _audioStreamSub = audioStream.listen(
    (data) {
      _updateMicLevel(data);
      _frameBuffer.addAll(data);
      while (_frameBuffer.length >= _framesPerMessage * _frameBytes) {
        final chunk = _frameBuffer.sublist(0, _framesPerMessage * _frameBytes);
        _frameBuffer.removeRange(0, _framesPerMessage * _frameBytes);
        _sendAudioFrame(chunk);
      }
    },
    onDone: () => print('[Voice] Audio stream ended'),
    onError: (e) => print('[Voice] Audio stream error: $e'),
  );
}

void _updateMicLevel(List<int> pcm) {
  final raw = VoiceService.rms(pcm);
  final alpha = raw > _smoothedMicLevel ? 0.4 : 0.15;
  _smoothedMicLevel += (raw - _smoothedMicLevel) * alpha;
  if (!_micLevelController.isClosed) _micLevelController.add(_smoothedMicLevel);
}
```

In `dispose()`, after closing `_phaseController` (line ~500), add:

```dart
if (!_micLevelController.isClosed) _micLevelController.close();
```

- [ ] **Step 6: Run voice tests to verify nothing broke**

Run: `C:\flutter\bin\flutter.bat test test/voice_service_rms_test.dart`
Expected: PASS (3/3).

- [ ] **Step 7: Commit**

```bash
git add client/lib/services/voice_service.dart client/test/voice_service_rms_test.dart
git commit -m "feat(voice): smoothed mic RMS stream for reactive avatar"
```

---

### Task 4: Rewrite avatar as radial equalizer + parallax

**Files:**
- Modify: `client/lib/widgets/avatar_widget.dart`
- Test: `client/test/avatar_widget_test.dart`

**Interfaces:**
- Consumes: `Stream<double> micLevel` (Task 3), `Stream<Offset> tilt` (Task 2), `AppTheme.phaseColor` / `AppTheme.dataFont` (existing).
- Produces: `AvatarWidget({super.key, required String currentState, bool wordPulse, Stream<double>? micLevel, Stream<Offset>? tilt})` — old params unchanged. `JarvisHudPainter` adds `bars` (List\<double\>), `tiltX`, `tiltY`. Task 5 consumes the two new streams.

- [ ] **Step 1: Extend the failing widget test**

```dart
import 'dart:async';
import 'dart:ui' as ui;

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

  testWidgets('AvatarWidget reacts to micLevel and tilt streams', (tester) async {
    final mic = StreamController<double>.broadcast();
    final tilt = StreamController<Offset>.broadcast();
    addTearDown(() {
      mic.close();
      tilt.close();
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Center(
          child: AvatarWidget(
            currentState: 'listening',
            wordPulse: false,
            micLevel: mic.stream,
            tilt: tilt.stream,
          ),
        ),
      ),
    );

    mic.add(0.7);
    tilt.add(const Offset(0.5, -0.3));
    await tester.pump(const Duration(milliseconds: 250));

    expect(tester.takeException(), isNull);
  });

  test('JarvisHudPainter paints with bars and tilt', () {
    final painter = JarvisHudPainter(
      progress: 0.5,
      state: 'idle',
      bars: List.filled(44, 0.5),
      tiltX: 0.5,
      tiltY: -0.3,
    );
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder);
    painter.paint(canvas, const Size(300, 300));
    recorder.endRecording();
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\flutter\bin\flutter.bat test test/avatar_widget_test.dart`
Expected: FAIL — `JarvisHudPainter` constructor has no `bars`/`tiltX`/`tiltY`; `AvatarWidget` has no `micLevel`/`tilt`.

- [ ] **Step 3: Rewrite `avatar_widget.dart`**

Replace the entire file:

```dart
import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import '../utils/theme.dart';

class AvatarWidget extends StatefulWidget {
  final String currentState;
  final bool wordPulse;
  final Stream<double>? micLevel;
  final Stream<Offset>? tilt;

  const AvatarWidget({
    super.key,
    required this.currentState,
    this.wordPulse = false,
    this.micLevel,
    this.tilt,
  });

  @override
  State<AvatarWidget> createState() => _AvatarWidgetState();
}

class _AvatarWidgetState extends State<AvatarWidget>
    with TickerProviderStateMixin {
  late AnimationController _controller;
  StreamSubscription<double>? _micSub;
  StreamSubscription<Offset>? _tiltSub;
  double _latestMicLevel = 0.0;
  Offset _tilt = Offset.zero;

  static const int _barCount = 44;
  static const List<double> _barWeights = [
    0.55, 0.40, 0.70, 0.35, 0.85, 0.50, 0.30, 0.65,
    0.45, 0.80, 0.38, 0.60, 0.52, 0.33, 0.78, 0.42,
    0.68, 0.30, 0.58, 0.47, 0.88, 0.36, 0.62, 0.44,
    0.75, 0.28, 0.66, 0.53, 0.40, 0.72, 0.34, 0.82,
    0.48, 0.60, 0.31, 0.69, 0.43, 0.76, 0.50, 0.38,
    0.64, 0.46, 0.57, 0.35,
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 8),
      vsync: this,
    )..repeat();
    _updateSpeed();
    _subscribe();
  }

  @override
  void didUpdateWidget(AvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentState != widget.currentState) {
      _updateSpeed();
    }
    if (oldWidget.micLevel != widget.micLevel ||
        oldWidget.tilt != widget.tilt) {
      _subscribe();
    }
  }

  void _subscribe() {
    _micSub?.cancel();
    _tiltSub?.cancel();
    _micSub = widget.micLevel?.listen((v) => _latestMicLevel = v.clamp(0.0, 1.0));
    _tiltSub = widget.tilt?.listen((v) => _tilt = v);
  }

  void _updateSpeed() {
    switch (widget.currentState) {
      case 'idle':
        _controller.duration = const Duration(seconds: 8);
        break;
      case 'listening':
        _controller.duration = const Duration(seconds: 3);
        break;
      case 'thinking':
        _controller.duration = const Duration(milliseconds: 600);
        break;
      case 'speaking':
        _controller.duration = const Duration(seconds: 4);
        break;
      case 'error':
        _controller.duration = const Duration(milliseconds: 400);
        break;
    }
  }

  @override
  void dispose() {
    _micSub?.cancel();
    _tiltSub?.cancel();
    _controller.dispose();
    super.dispose();
  }

  List<double> _buildBars() {
    final t = _controller.value;
    final list = List<double>.filled(_barCount, 0.08);
    switch (widget.currentState) {
      case 'idle':
        for (var i = 0; i < _barCount; i++) {
          list[i] = 0.08 + 0.12 * (0.5 + 0.5 * math.sin(t * 2 * math.pi + i * 0.9));
        }
        break;
      case 'listening':
        for (var i = 0; i < _barCount; i++) {
          list[i] = 0.05 + _latestMicLevel * 0.95 * _barWeights[i];
        }
        break;
      case 'thinking':
        for (var i = 0; i < _barCount; i++) {
          list[i] = 0.2 + 0.6 * (0.5 + 0.5 * math.sin(t * 18 * math.pi + i * 0.5));
        }
        break;
      case 'speaking':
        for (var i = 0; i < _barCount; i++) {
          final wave = 0.5 + 0.5 * math.sin(t * 6 * math.pi + i * 0.7);
          list[i] = 0.15 + wave * (widget.wordPulse ? 0.85 : 0.35);
        }
        break;
      case 'error':
        for (var i = 0; i < _barCount; i++) {
          list[i] = math.sin(t * 40 + i * 3.1) > 0 ? 0.9 : 0.1;
        }
        break;
    }
    return list;
  }

  @override
  Widget build(BuildContext context) {
    final reduced = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return FittedBox(
          fit: BoxFit.contain,
          child: SizedBox(
            width: 300,
            height: 300,
            child: CustomPaint(
              size: const Size(300, 300),
              painter: JarvisHudPainter(
                progress: _controller.value,
                state: widget.currentState,
                wordPulse: widget.wordPulse,
                slowFactor: reduced ? 0.15 : 1.0,
                bars: _buildBars(),
                tiltX: _tilt.dx,
                tiltY: _tilt.dy,
              ),
            ),
          ),
        );
      },
    );
  }
}

class JarvisHudPainter extends CustomPainter {
  final double progress;
  final String state;
  final bool wordPulse;
  final double slowFactor;
  final List<double> bars;
  final double tiltX;
  final double tiltY;

  JarvisHudPainter({
    required this.progress,
    required this.state,
    this.wordPulse = false,
    this.slowFactor = 1.0,
    this.bars = const [],
    this.tiltX = 0.0,
    this.tiltY = 0.0,
  });

  static const _r = 150.0;
  static const _cx = 150.0;
  static const _cy = 150.0;
  static const _center = Offset(_cx, _cy);

  static const double _maxShift = 12.0;

  Color get _tint => AppTheme.phaseColor(state);

  double get _speed {
    switch (state) {
      case 'idle':
        return 0.4;
      case 'listening':
        return 1.2;
      case 'thinking':
        return 3.0;
      case 'speaking':
        return 0.8;
      case 'error':
        return 2.5;
      default:
        return 0.6;
    }
  }

  String get _phaseLabel {
    switch (state) {
      case 'listening':
        return 'SCANNING';
      case 'thinking':
        return 'PROCESSING';
      case 'speaking':
        return 'VOICE OUTPUT';
      case 'error':
        return 'SYSTEM FAULT';
      default:
        return 'ALL SYSTEMS FUNCTIONING';
    }
  }

  Offset _depth(double depth) {
    final dir = Offset(-tiltX, -tiltY);
    return dir * (depth * _maxShift);
  }

  @override
  void paint(Canvas canvas, Size size) {
    final t = progress * _speed * slowFactor;
    final breathe = 1.0 + 0.012 * math.sin(t * math.pi * 0.5);
    final pulse = wordPulse
        ? 1.0 + 0.28 * (0.5 + 0.5 * math.sin(t * 6 * math.pi))
        : 1.0;

    _drawBgFog(canvas, t, _depth(1));
    _drawCornerBrackets(canvas, t, _depth(1));
    _drawTickRing(canvas, t, breathe, _depth(1));
    _drawSegmentedRings(canvas, t, breathe, _depth(2));
    _drawEqualizer(canvas, t, breathe, _depth(2));
    _drawCore(canvas, t, pulse, _depth(3));
    _drawReadouts(canvas, t, _depth(1));
    _drawWordmark(canvas, t, _depth(1));
  }

  void _drawBgFog(Canvas canvas, double t, Offset depth) {
    canvas.save();
    canvas.translate(depth.dx * 0.3, depth.dy * 0.3);
    canvas.drawCircle(
      _center, _r,
      Paint()
        ..shader = RadialGradient(
          colors: [_tint.withValues(alpha: 0.05), _tint.withValues(alpha: 0)],
        ).createShader(Rect.fromCircle(center: _center, radius: _r)),
    );
    canvas.restore();
  }

  void _drawCornerBrackets(Canvas canvas, double t, Offset depth) {
    final blink = 0.6 + 0.4 * math.sin(t * 2 * math.pi);
    const positions = [
      [-1.0, -1.0, 0.0],
      [1.0, -1.0, math.pi / 2],
      [1.0, 1.0, math.pi],
      [-1.0, 1.0, -math.pi / 2],
    ];
    final bracketR = _r * 0.95;
    final size = _r * 0.06;
    final gap = _r * 0.015;
    for (final p in positions) {
      canvas.save();
      canvas.translate(_cx + depth.dx + p[0] * bracketR,
          _cy + depth.dy + p[1] * bracketR);
      canvas.rotate(p[2]);
      final paint = Paint()
        ..color = _tint.withValues(alpha: 0.45 * blink)
        ..strokeWidth = 1.5;
      canvas.drawLine(Offset(-size - gap, -gap), Offset(-gap, -gap), paint);
      canvas.drawLine(Offset(-gap, -gap), Offset(-gap, -size - gap), paint);
      canvas.restore();
    }
  }

  void _drawTickRing(Canvas canvas, double t, double breathe, Offset depth) {
    const count = 40;
    final tickR = _r * 0.92 * breathe;
    final activeOffset = (t * 4).round() % count;
    for (int i = 0; i < count; i++) {
      final a = i * 2 * math.pi / count;
      final lit = ((i - activeOffset) % count) < 5;
      final innerR = tickR * (lit ? 0.94 : 0.96);
      final outerR = tickR * (lit ? 1.0 : 0.99);
      canvas.drawLine(
        Offset(_cx + depth.dx + math.cos(a) * innerR,
            _cy + depth.dy + math.sin(a) * innerR),
        Offset(_cx + depth.dx + math.cos(a) * outerR,
            _cy + depth.dy + math.sin(a) * outerR),
        Paint()
          ..color = _tint.withValues(alpha: lit ? 0.7 : 0.12)
          ..strokeWidth = lit ? 1.4 : 0.6,
      );
    }
    canvas.drawLine(
      Offset(_cx + depth.dx, _cy + depth.dy - tickR - 2),
      Offset(_cx + depth.dx, _cy + depth.dy - tickR - 8),
      Paint()
        ..color = _tint.withValues(alpha: 0.8 + 0.2 * math.sin(t * 2 * math.pi))
        ..strokeWidth = 2,
    );
  }

  void _drawSegmentedRings(Canvas canvas, double t, double breathe, Offset depth) {
    final specs = <({double radius, double start, double width, double alpha})>[
      (radius: _r * 0.82, start: t * 0.5, width: 1.4, alpha: 0.35),
      (radius: _r * 0.60, start: -t * 0.7, width: 1.0, alpha: 0.25),
    ];
    for (final s in specs) {
      final rr = s.radius * breathe;
      final paint = Paint()
        ..color = _tint.withValues(alpha: s.alpha)
        ..style = PaintingStyle.stroke
        ..strokeWidth = s.width
        ..strokeCap = StrokeCap.round;
      for (int seg = 0; seg < 3; seg++) {
        final start = s.start + seg * (2 * math.pi / 3);
        canvas.drawArc(
          Rect.fromCircle(
              center: _center + depth, radius: rr),
          start, 0.45, false, paint,
        );
      }
    }
  }

  void _drawEqualizer(Canvas canvas, double t, double breathe, Offset depth) {
    const count = 44;
    final baseR = _r * 0.68 * breathe;
    final center = _center + depth;
    for (int i = 0; i < count; i++) {
      final a = i * 2 * math.pi / count + t * 0.05;
      final amp = (bars.isEmpty ? 0.3 : bars[i]).clamp(0.0, 1.0);
      final base = baseR - 3.0 * amp;
      final tip = baseR + 10.0 + 16.0 * amp;
      final paint = Paint()
        ..color = _tint.withValues(alpha: 0.35 + 0.65 * amp)
        ..strokeWidth = 2.2
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(
        Offset(center.dx + math.cos(a) * base, center.dy + math.sin(a) * base),
        Offset(center.dx + math.cos(a) * tip, center.dy + math.sin(a) * tip),
        paint,
      );
    }
  }

  void _drawCore(Canvas canvas, double t, double pulse, Offset depth) {
    final p = 0.5 + 0.5 * math.sin(t * 2 * math.pi);
    final coreR = _r * 0.12;
    final center = _center + depth;

    canvas.drawCircle(
      center, coreR * 2.6,
      Paint()
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, 18 + p * 8)
        ..shader = RadialGradient(
          colors: [
            _tint.withValues(alpha: 0.35 + p * 0.15),
            _tint.withValues(alpha: 0.05),
            _tint.withValues(alpha: 0),
          ],
        ).createShader(Rect.fromCircle(center: center, radius: coreR * 2.6)),
    );

    final spoke = Paint()
      ..color = _tint.withValues(alpha: 0.5)
      ..strokeWidth = 1.2
      ..strokeCap = StrokeCap.round;
    for (int i = 0; i < 3; i++) {
      final a = i * 2 * math.pi / 3 + t * 0.05;
      canvas.drawLine(
        Offset(center.dx + math.cos(a) * coreR * 0.25,
            center.dy + math.sin(a) * coreR * 0.25),
        Offset(center.dx + math.cos(a) * coreR * 0.9,
            center.dy + math.sin(a) * coreR * 0.9),
        spoke,
      );
    }

    canvas.drawCircle(
      center, coreR,
      Paint()
        ..color = _tint.withValues(alpha: 0.9)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, 3),
    );
    canvas.drawCircle(
      center, coreR * 0.82,
      Paint()
        ..color = Colors.white.withValues(alpha: 0.8)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2,
    );
    canvas.drawCircle(
      center, coreR * 0.55 * (1.0 + p * 0.08 * pulse),
      Paint()
        ..shader = RadialGradient(
          colors: [
            Colors.white.withValues(alpha: 1.0),
            _tint.withValues(alpha: 0.9),
            _tint.withValues(alpha: 0.3),
          ],
        ).createShader(Rect.fromCircle(center: center, radius: coreR)),
    );
  }

  void _drawReadouts(Canvas canvas, double t, Offset depth) {
    final alpha = 0.35 + 0.15 * (0.5 + 0.5 * math.sin(t * math.pi * 1.3));
    final style = TextStyle(
      color: _tint.withValues(alpha: alpha),
      fontSize: 8,
      letterSpacing: 2.5,
      fontFamily: AppTheme.dataFont,
      fontWeight: FontWeight.w300,
    );
    final cx = _cx + depth.dx;
    final cy = _cy + depth.dy;
    _label(canvas, 'SYS ONLINE', cx, cy - _r * 0.46, style);
    _label(canvas, _phaseLabel, cx, cy + _r * 0.46, style);
    _label(canvas, 'TGT: ACQ', cx - _r * 0.62, cy, style);
    _label(canvas, 'PWR: 100%', cx + _r * 0.62, cy, style);
  }

  void _label(Canvas canvas, String text, double x, double y, TextStyle style) {
    final tp = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
    );
    tp.layout();
    tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
  }

  void _drawWordmark(Canvas canvas, double t, Offset depth) {
    final opacity = 0.55 + 0.25 * (0.5 + 0.5 * math.sin(t * math.pi));
    final style = TextStyle(
      color: _tint.withValues(alpha: opacity),
      fontSize: 12,
      letterSpacing: 6,
      fontFamily: AppTheme.dataFont,
      fontWeight: FontWeight.w400,
    );
    final cx = _cx + depth.dx;
    final cy = _cy + depth.dy;
    final wordY = cy + _r * 0.78;
    _label(canvas, 'J.A.R.V.I.S.', cx, wordY, style);
    canvas.drawLine(
      Offset(cx - _r * 0.2, wordY + 16),
      Offset(cx + _r * 0.2, wordY + 16),
      Paint()
        ..color = _tint.withValues(alpha: opacity * 0.5)
        ..strokeWidth = 1,
    );
  }

  @override
  bool shouldRepaint(covariant JarvisHudPainter old) =>
      old.progress != progress ||
      old.state != state ||
      old.wordPulse != wordPulse ||
      old.slowFactor != slowFactor ||
      old.tiltX != tiltX ||
      old.tiltY != tiltY ||
      old.bars != bars;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `C:\flutter\bin\flutter.bat test test/avatar_widget_test.dart`
Expected: PASS — 5 states + reduced motion + micLevel/tilt stream test + painter test.

- [ ] **Step 5: Commit**

```bash
git add client/lib/widgets/avatar_widget.dart client/test/avatar_widget_test.dart
git commit -m "feat(avatar): radial equalizer waveform + tilt parallax"
```

---

### Task 5: Wire motion + mic level into home screen

**Files:**
- Modify: `client/lib/screens/home_screen.dart`

**Interfaces:**
- Consumes: `MotionService` (Task 2), `voiceService.micLevel` (Task 3), new `AvatarWidget` params (Task 4).
- Produces: Home screen avatar driven by live tilt + mic level. No new widget API.

- [ ] **Step 1: Add imports and motion field**

Add to the imports (after line 8 `voice_service.dart`):

```dart
import '../services/motion_service.dart';
```

Add a field in `_HomeScreenState` (near line 39, after `_voicePhase`):

```dart
MotionService? _motionService;
```

- [ ] **Step 2: Start motion in `initState`, stop in `dispose`**

At the end of `initState` (after `_setupConnectionWatch()`, line ~63), add:

```dart
_motionService = MotionService();
_motionService?.start();
```

Add `_motionService?.stop();` to the existing `dispose()` override (currently at line ~195, after `_stopWordPulse()`):

```dart
@override
void dispose() {
  _motionService?.stop();
  _stopWordPulse();
  _avatarSubscription?.cancel();
  _transcriptionSubscription?.cancel();
  _responseSubscription?.cancel();
  _phaseSubscription?.cancel();
  _messageSubscription?.cancel();
  _ttsDoneSubscription?.cancel();
  _chatController.dispose();
  _chatScrollController.dispose();
  super.dispose();
}
```

- [ ] **Step 3: Pass streams to AvatarWidget**

In `_buildAvatarSection`, update the `AvatarWidget` (currently at line ~275):

```dart
AvatarWidget(
  currentState: _avatarState,
  wordPulse: _wordPulse,
  micLevel: _voiceService.micLevel,
  tilt: _motionService?.tilt,
),
```

- [ ] **Step 4: Run tests + analyze**

Run: `C:\flutter\bin\flutter.bat test`
Expected: smoke test + all widget tests pass.

Run: `C:\flutter\bin\flutter.bat analyze`
Expected: no new errors; pre-existing warnings (unused `_hudDim`/`_lastMessage`/`_transcription`) may remain.

- [ ] **Step 5: Commit**

```bash
git add client/lib/screens/home_screen.dart
git commit -m "feat(home): drive avatar from mic RMS and tilt"
```

---

### Task 6: Final verification

**Files:**
- Modify: none (verification only)

- [ ] **Step 1: Full test suite**

Run: `C:\flutter\bin\flutter.bat test`
Expected: all tests pass.

- [ ] **Step 2: Full static analysis**

Run: `C:\flutter\bin\flutter.bat analyze`
Expected: no errors; no NEW warnings beyond the pre-existing baseline.

- [ ] **Step 3: Visual check on the phone**

Run the app on the Android device. Confirm:
- Avatar shows a radial equalizer ring of 44 bars around the core.
- Listening → bars jump with your voice (real mic RMS).
- Speaking → bars ripple procedurally, pulsing with each word.
- Thinking → fast amber flicker; error → red jitter; idle → calm cyan ripple.
- Tilt the phone → core shifts ~12 px, bars/rings ~8 px, chrome ~4 px (parallax, opposite the tilt).

- [ ] **Step 4: Update knowledge graph**

Run: `& "C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\graphify.exe" update .`
Expected: graph rebuilt.

- [ ] **Step 5: Commit any leftovers**

```bash
git add -A
git commit -m "chore: finalize reactive waveform avatar"
```
(Only if there are uncommitted changes from the visual-check fixes.)
