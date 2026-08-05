# Reactive Waveform JARVIS Avatar — Design

**Date:** 2026-08-05
**Status:** Approved (design gate passed)

## Overview

Evolve the arc-reactor JARVIS avatar into a **radial equalizer**: a circular
spectrum-analyzer ring of bars driven by real microphone level while listening,
procedural animation while speaking/thinking. Add a **motion parallax** effect:
tilting the phone shifts the avatar's internal layers at different depths.

## Requirements (from brainstorming)

- **Different look:** radial equalizer (40–48 bars in a circle, small glowing
  core at center, existing HUD chrome around it).
- **Waveform data:** real mic RMS while listening (computed client-side from PCM
  frames already streamed); procedural (sin waves + `wordPulse`) while speaking
  and thinking; gentle ambient ripple at idle; red jitter at error.
- **Parallax:** tilt-follow driven by the Android accelerometer gravity vector.
  Internal layers only — no whole-avatar slide. Android only; Windows desktop
  stays static.
- **More HUD detail + stronger phase reactions** than the current arc-reactor.
- Phase colors/speeds unchanged: idle cyan `#40F9FF` (8s), listening green
  `#00FF88` (3s), thinking amber `#FFB300` (600ms), speaking white (4s), error
  red `#FF4444` (400ms).
- **No new dependencies** — native Android sensors via a hand-written Kotlin
  plugin (Ponytail rung 3), matching the existing `MicRecorderPlugin` /
  `TTSPlugin` pattern.
- Respect reduced motion (`slowFactor` 0.15) as today.

## Section 1 — Sensor layer (Android)

### `client/android/app/src/main/kotlin/com/jarvis/jarvis_app/MotionSensorPlugin.kt` (new)

- Implements `MethodChannel.MethodCallHandler` + `EventChannel.StreamHandler`.
- Registers `SensorManager.getSensorList(TYPE_ACCELEROMETER)`.
- Applies a low-pass filter on raw accelerometer readings to extract the gravity
  vector: `g = g * alpha + raw * (1 - alpha)` with `alpha ≈ 0.1`.
- Normalizes each axis to `[-1, 1]` (roughly `-2..2 m/s²` over the gravity
  offset maps to the tilt range) and emits `[tx, ty]` as a `DoubleArray` on the
  event sink.
- Emission rate ~30 Hz via `Handler`; sensor unregistered on `onCancel`.
- **No permission required** (accelerometer is a non-dangerous sensor).

### `MainActivity.kt`

Register the plugin exactly like `micRecorderPlugin`:
- Method channel `motion_sensor` → `onMethodCall`.
- Event channel `motion_sensor_events` → `setStreamHandler(motionSensorPlugin)`.
- Methods: `start` (register listener), `stop` (unregister).

### `client/lib/services/motion_service.dart` (new)

- `MotionService` wraps the two channels.
- `Stream<Offset> get tilt` — `EventChannel` receiveBroadcastStream mapped to
  `Offset(tx, ty)`; on non-Android platforms returns a static zero stream so
  desktop rendering is unchanged.
- `Future<bool> start() / stop()`.
- Internal normalization/rounding: clamp to `[-1, 1]`, emit only on change
  > 0.01 to limit rebuild churn.

## Section 2 — Waveform data (mic RMS)

### `client/lib/services/voice_service.dart`

- In `_processAudioStream`, before forwarding each PCM chunk, compute RMS:
  `sqrt(mean(sample^2))` over the s16le samples; normalize to 0–1
  (divide by 32768).
- Smooth with an attack/decay envelope (attack ~30 ms, decay ~150 ms) to avoid
  harsh bar jumps.
- Publish via a new broadcast `StreamController<double>`; expose
  `Stream<double> get micLevel`.
- Add a pure static helper `static double rms(List<int> pcmBytes)` (unit-testable).

### `AvatarWidget` API

```dart
const AvatarWidget({
  super.key,
  required this.currentState,
  this.wordPulse = false,
  this.micLevel,          // Stream<double>?, real mic RMS 0..1
  this.tilt,              // Stream<Offset>?, normalized parallax
});
```

- When `micLevel` is null/absent, listening uses procedural animation (the
  Windows path and default).
- Home screen passes `voiceService.micLevel` and `motionService.tilt`.
- **Bar computation:** the widget state stores `_latestMicLevel` (a single
  `double`, updated whenever the stream emits) and derives the `bars` list
  per-frame inside the `AnimatedBuilder` builder from `phase + _latestMicLevel +
  progress`. The painter stays pure: it receives a concrete `bars` list.

## Section 3 — Painter rewrite (`JarvisHudPainter`)

Same 300×300 canvas (center 150,150), same `progress / state / wordPulse /
slowFactor` public fields, plus:
- `final double tiltX, tiltY;` — normalized `[-1, 1]`.
- `final List<double> bars;` — per-bar amplitudes (defaults to procedural when
  empty).

### Composition (draw order)

1. **Background fog** — radial tint gradient (existing), depth 1.
2. **Tick ring** — existing 40-tick perimeter, lit sweep, depth 1.
3. **Corner brackets** — existing blinking helmet brackets, depth 1.
4. **Segmented rings** — two thin rotating dashed arcs, depth 2.
5. **Radial equalizer (NEW)** — 44 bars arranged in a circle at r≈0.70×R, each a
   rounded line segment extending outward from its base radius; length scales
   with `bars[i]`. Depth 2.
6. **Core** — small arc-reactor core (existing), brighter, swells with
   `wordPulse`. Depth 3.
7. **Readouts + wordmark** — existing, depth 1 (fixed, only tiny drift).

### Waveform behavior per phase

| phase | equalizer drive |
|---|---|
| idle | gentle ambient sine ripple, slow (0.05–0.2 amplitude) |
| listening | real mic RMS per bar (spread via pseudo-random fixed weights), 3 lit bars sweep the ring |
| thinking | fast procedural flicker (amplitude 0.4–1.0), rings spin fast |
| speaking | procedural sin waves, bars pulse with `wordPulse` |
| error | red jitter, quick random flips |

Bar updates run in the existing `AnimatedBuilder` (single controller); mic RMS
is smoothed client-side so no separate timer is needed.

### Parallax

`offset = Offset(tiltX, tiltY) * layerDepth * maxShift` with `maxShift ≈ 12 px`
at depth 3; drawn opposite the tilt (device tilts right → layers shift left).

| layer | depth | shift |
|---|---|---|
| fog, tick ring, brackets, readouts, wordmark | 1 | ~4 px |
| segmented rings, equalizer bars | 2 | ~8 px |
| core | 3 | ~12 px |

All internal to the canvas — nothing moves the widget's layout box.

## Section 4 — Home screen wiring

- `_HomeScreenState` instantiates `MotionService` (Android only path), calls
  `start()` in `initState`, `stop()` in `dispose`.
- Subscribes `motionService.tilt` → passes to `AvatarWidget.tilt`.
- Passes `_voiceService.micLevel` → `AvatarWidget.micLevel`.
- No layout, navigation, or behavior changes.

## Section 5 — Testing

- `client/test/avatar_widget_test.dart` — existing 5-phase + reduced-motion
  tests stay; add: painter paints with non-empty `bars` without exception;
  painter paints with non-zero `tiltX/tiltY` without exception.
- `client/test/motion_service_test.dart` (new) — fake EventChannel emits
  `[0.5, -0.3]` → stream emits `Offset(0.5, -0.3)`; emits zero on unsupported
  platforms; filters noise (no emit when delta < 0.01).
- `client/test/voice_service_rms_test.dart` (new) — `rms()` of silence = 0;
  full-scale square = 1.0; known sample values.
- `flutter analyze` — no new errors/warnings.
- `flutter test` — all pass.
- Visual check: run on the phone, tilt device, confirm core shifts most, bars
  react to voice while listening.

## Out of scope

- No changes to backend, wake word, STT/TTS pipeline, or other screens.
- No changes to compact avatar widget.
- No new dependencies.
- No layout/navigation changes.
