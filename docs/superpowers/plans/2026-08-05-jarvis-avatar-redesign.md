# Iron Man JARVIS Avatar Redesign + App Theme — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the JARVIS avatar as an Iron Man 2 arc-reactor HUD (with distinct per-phase colors) and apply a shared cyan-on-near-black theme across the whole Flutter app.

**Architecture:** A new `AppTheme` token class in `lib/utils/theme.dart` becomes the single color/type source of truth. The `JarvisHudPainter` in `avatar_widget.dart` is rebuilt from scratch (still one `CustomPainter` + one `AnimationController`, same public API). Every screen keeps its current layout and just consumes theme tokens instead of local `Color(...)` constants.

**Tech Stack:** Flutter / Dart, `CustomPainter`, existing dev deps (`flutter_test`, `flutter_lints`). No new dependencies.

## Global Constraints

- No new dependencies — stdlib/Flutter only (Ponytail rung 4/6).
- Preserve layout, navigation, and behavior in every screen — cosmetic color/typography changes only.
- `AvatarWidget`/`JarvisHudPainter` public API stays: `AvatarWidget({required String currentState, bool wordPulse})` — callers in `home_screen.dart` must not change.
- Phase colors are fixed: idle `#40F9FF`, listening `#00FF88`, thinking `#FFB300`, speaking `#FFFFFF`, error `#FF4444`.
- Respect reduced motion: when `MediaQuery.maybeOf(context)?.disableAnimations` is true, animation slows to 15%.
- Import path for theme: `../utils/theme.dart` from `lib/screens/*`, `lib/widgets/*`, `lib/overlay/*`; `utils/theme.dart` from `lib/main.dart`.
- Flutter is NOT on PATH — run via `C:\flutter\bin\flutter.bat`.
- Spec: `docs/superpowers/specs/2026-08-05-jarvis-avatar-redesign-design.md`

---

### Task 1: Create theme token file

**Files:**
- Create: `client/lib/utils/theme.dart`
- Test: `client/test/theme_test.dart`

**Interfaces:**
- Consumes: nothing.
- Produces: `AppTheme` with `static const Color bg, panel, panelAlt, hud, hudDim, hudGlow, text, textDim, accentGreen, accentAmber, accentRed`; `static const String dataFont`; `static Color phaseColor(String state)`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_app/utils/theme.dart';

void main() {
  test('phaseColor returns a distinct color for every phase', () {
    final colors = {
      'idle': AppTheme.phaseColor('idle'),
      'listening': AppTheme.phaseColor('listening'),
      'thinking': AppTheme.phaseColor('thinking'),
      'speaking': AppTheme.phaseColor('speaking'),
      'error': AppTheme.phaseColor('error'),
    };
    expect(colors.values.toSet().length, 5);
    expect(colors['idle'], AppTheme.hud);
    expect(colors['listening'], AppTheme.accentGreen);
    expect(colors['thinking'], AppTheme.accentAmber);
    expect(colors['speaking'], Colors.white);
    expect(colors['error'], AppTheme.accentRed);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\flutter\bin\flutter.bat test test/theme_test.dart`
Expected: FAIL — `Undefined class 'AppTheme'`.

- [ ] **Step 3: Write minimal implementation**

```dart
import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  static const Color bg = Color(0xFF050810);
  static const Color panel = Color(0xFF0A0E1A);
  static const Color panelAlt = Color(0xFF121A2E);
  static const Color hud = Color(0xFF40F9FF);
  static const Color hudDim = Color(0xFF0099CC);
  static const Color hudGlow = Color(0xFF00E5FF);
  static const Color text = Color(0xFFE8F6FF);
  static const Color textDim = Color(0xFF7A8BA8);

  static const Color accentGreen = Color(0xFF00FF88);
  static const Color accentAmber = Color(0xFFFFB300);
  static const Color accentRed = Color(0xFFFF4444);

  static const String dataFont = 'monospace';

  static Color phaseColor(String state) {
    switch (state) {
      case 'listening':
        return accentGreen;
      case 'thinking':
        return accentAmber;
      case 'speaking':
        return Colors.white;
      case 'error':
        return accentRed;
      default:
        return hud;
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\flutter\bin\flutter.bat test test/theme_test.dart`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add client/lib/utils/theme.dart client/test/theme_test.dart
git commit -m "feat(theme): add Iron Man JARVIS theme tokens"
```

---

### Task 2: Rebuild the avatar as an arc-reactor HUD

**Files:**
- Rewrite: `client/lib/widgets/avatar_widget.dart`
- Test: `client/test/avatar_widget_test.dart`

**Interfaces:**
- Consumes: `AppTheme.phaseColor`, `AppTheme.dataFont` (Task 1).
- Produces: `AvatarWidget` — unchanged constructor `AvatarWidget({super.key, required this.currentState, this.wordPulse = false})`. `JarvisHudPainter` gains optional `slowFactor` (default 1.0).

- [ ] **Step 1: Write the failing widget test**

```dart
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
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\flutter\bin\flutter.bat test test/avatar_widget_test.dart`
Expected: Existing painter still passes render, but the reduced-motion test is new behavior (will currently be unverifiable) — confirm test compiles and runs. If it passes already, that is fine for this refactor; the real gate is Task 2's behavior review + visual check in Task 6.

- [ ] **Step 3: Rewrite `avatar_widget.dart`**

Replace the entire file (keep class names `AvatarWidget`, `JarvisHudPainter`). Full implementation:

```dart
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../utils/theme.dart';

class AvatarWidget extends StatefulWidget {
  final String currentState;
  final bool wordPulse;

  const AvatarWidget({super.key, required this.currentState, this.wordPulse = false});

  @override
  State<AvatarWidget> createState() => _AvatarWidgetState();
}

class _AvatarWidgetState extends State<AvatarWidget>
    with TickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 8),
      vsync: this,
    )..repeat();
  }

  @override
  void didUpdateWidget(AvatarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentState != widget.currentState) {
      _updateSpeed();
    }
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
    _controller.dispose();
    super.dispose();
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

  JarvisHudPainter({
    required this.progress,
    required this.state,
    this.wordPulse = false,
    this.slowFactor = 1.0,
  });

  static const _r = 150.0;
  static const _cx = 150.0;
  static const _cy = 150.0;
  static const _center = Offset(_cx, _cy);

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

  @override
  void paint(Canvas canvas, Size size) {
    final t = progress * _speed * slowFactor;
    final breathe = 1.0 + 0.012 * math.sin(t * math.pi * 0.5);
    final pulse = wordPulse
        ? 1.0 + 0.28 * (0.5 + 0.5 * math.sin(t * 6 * math.pi))
        : 1.0;

    _drawBgFog(canvas, t);
    _drawCornerBrackets(canvas, t);
    _drawTickRing(canvas, t, breathe);
    _drawSegmentedRings(canvas, t, breathe);
    _drawParticleStreams(canvas, t, breathe);
    _drawCore(canvas, t, pulse);
    _drawReadouts(canvas, t);
    _drawWordmark(canvas, t);
  }

  void _drawBgFog(Canvas canvas, double t) {
    canvas.drawCircle(
      _center, _r,
      Paint()
        ..shader = RadialGradient(
          colors: [_tint.withValues(alpha: 0.05), _tint.withValues(alpha: 0)],
        ).createShader(Rect.fromCircle(center: _center, radius: _r)),
    );
  }

  void _drawCornerBrackets(Canvas canvas, double t) {
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
      canvas.translate(_cx + p[0] * bracketR, _cy + p[1] * bracketR);
      canvas.rotate(p[2] as double);
      final paint = Paint()
        ..color = _tint.withValues(alpha: 0.45 * blink)
        ..strokeWidth = 1.5;
      canvas.drawLine(Offset(-size - gap, -gap), Offset(-gap, -gap), paint);
      canvas.drawLine(Offset(-gap, -gap), Offset(-gap, -size - gap), paint);
      canvas.restore();
    }
  }

  void _drawTickRing(Canvas canvas, double t, double breathe) {
    const count = 40;
    final tickR = _r * 0.92 * breathe;
    final activeOffset = (t * 4).round() % count;
    for (int i = 0; i < count; i++) {
      final a = i * 2 * math.pi / count;
      final lit = ((i - activeOffset) % count) < 5;
      final innerR = tickR * (lit ? 0.94 : 0.96);
      final outerR = tickR * (lit ? 1.0 : 0.99);
      canvas.drawLine(
        Offset(_cx + math.cos(a) * innerR, _cy + math.sin(a) * innerR),
        Offset(_cx + math.cos(a) * outerR, _cy + math.sin(a) * outerR),
        Paint()
          ..color = _tint.withValues(alpha: lit ? 0.7 : 0.12)
          ..strokeWidth = lit ? 1.4 : 0.6,
      );
    }
    canvas.drawLine(
      Offset(_cx, _cy - tickR - 2),
      Offset(_cx, _cy - tickR - 8),
      Paint()
        ..color = _tint.withValues(alpha: 0.8 + 0.2 * math.sin(t * 2 * math.pi))
        ..strokeWidth = 2,
    );
  }

  void _drawSegmentedRings(Canvas canvas, double t, double breathe) {
    final specs = <({double radius, double start, double width, double alpha})>[
      (radius: _r * 0.72, start: t * 0.5, width: 1.4, alpha: 0.35),
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
          Rect.fromCircle(center: _center, radius: rr),
          start, 0.45, false, paint,
        );
      }
    }
  }

  void _drawParticleStreams(Canvas canvas, double t, double breathe) {
    final rings = <({double radius, int count, double speed, double alpha})>[
      (radius: _r * 0.80, count: 16, speed: 1.0, alpha: 0.55),
      (radius: _r * 0.52, count: 12, speed: -1.4, alpha: 0.7),
      (radius: _r * 0.33, count: 8, speed: 2.2, alpha: 0.85),
    ];
    for (final ring in rings) {
      final rr = ring.radius * breathe;
      for (int i = 0; i < ring.count; i++) {
        final a = i * 2 * math.pi / ring.count + t * ring.speed;
        final x = _cx + math.cos(a) * rr;
        final y = _cy + math.sin(a) * rr;
        final size = ring.count > 10 ? 1.6 : 2.2;
        canvas.drawCircle(
          Offset(x, y), size * 2.6,
          Paint()..color = _tint.withValues(alpha: ring.alpha * 0.15),
        );
        canvas.drawCircle(
          Offset(x, y), size,
          Paint()..color = _tint.withValues(alpha: ring.alpha),
        );
      }
    }
  }

  void _drawCore(Canvas canvas, double t, double pulse) {
    final p = 0.5 + 0.5 * math.sin(t * 2 * math.pi);
    final coreR = _r * 0.14;

    canvas.drawCircle(
      _center, coreR * 2.6,
      Paint()
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, 18 + p * 8)
        ..shader = RadialGradient(
          colors: [
            _tint.withValues(alpha: 0.35 + p * 0.15),
            _tint.withValues(alpha: 0.05),
            _tint.withValues(alpha: 0),
          ],
        ).createShader(Rect.fromCircle(center: _center, radius: coreR * 2.6)),
    );

    final spoke = Paint()
      ..color = _tint.withValues(alpha: 0.5)
      ..strokeWidth = 1.2
      ..strokeCap = StrokeCap.round;
    for (int i = 0; i < 3; i++) {
      final a = i * 2 * math.pi / 3 + t * 0.05;
      canvas.drawLine(
        Offset(_cx + math.cos(a) * coreR * 0.25, _cy + math.sin(a) * coreR * 0.25),
        Offset(_cx + math.cos(a) * coreR * 0.9, _cy + math.sin(a) * coreR * 0.9),
        spoke,
      );
    }

    canvas.drawCircle(
      _center, coreR,
      Paint()
        ..color = _tint.withValues(alpha: 0.9)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, 3),
    );
    canvas.drawCircle(
      _center, coreR * 0.82,
      Paint()
        ..color = Colors.white.withValues(alpha: 0.8)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2,
    );
    canvas.drawCircle(
      _center, coreR * 0.55 * (1.0 + p * 0.08 * pulse),
      Paint()
        ..shader = RadialGradient(
          colors: [
            Colors.white.withValues(alpha: 1.0),
            _tint.withValues(alpha: 0.9),
            _tint.withValues(alpha: 0.3),
          ],
        ).createShader(Rect.fromCircle(center: _center, radius: coreR)),
    );
  }

  void _drawReadouts(Canvas canvas, double t) {
    final alpha = 0.35 + 0.15 * (0.5 + 0.5 * math.sin(t * math.pi * 1.3));
    final style = TextStyle(
      color: _tint.withValues(alpha: alpha),
      fontSize: 8,
      letterSpacing: 2.5,
      fontFamily: AppTheme.dataFont,
      fontWeight: FontWeight.w300,
    );
    _label(canvas, 'SYS ONLINE', _cx, _cy - _r * 0.46, style);
    _label(canvas, _phaseLabel, _cx, _cy + _r * 0.46, style);
    _label(canvas, 'TGT: ACQ', _cx - _r * 0.62, _cy, style);
    _label(canvas, 'PWR: 100%', _cx + _r * 0.62, _cy, style);
  }

  void _label(Canvas canvas, String text, double x, double y, TextStyle style) {
    final tp = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
    );
    tp.layout();
    tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
  }

  void _drawWordmark(Canvas canvas, double t) {
    final opacity = 0.55 + 0.25 * (0.5 + 0.5 * math.sin(t * math.pi));
    final style = TextStyle(
      color: _tint.withValues(alpha: opacity),
      fontSize: 12,
      letterSpacing: 6,
      fontFamily: AppTheme.dataFont,
      fontWeight: FontWeight.w400,
    );
    final wordY = _cy + _r * 0.78;
    _label(canvas, 'J.A.R.V.I.S.', _cx, wordY, style);
    canvas.drawLine(
      Offset(_cx - _r * 0.2, wordY + 16),
      Offset(_cx + _r * 0.2, wordY + 16),
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
      old.slowFactor != slowFactor;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `C:\flutter\bin\flutter.bat test test/avatar_widget_test.dart`
Expected: PASS — all five states render, no exceptions, reduced-motion path renders.

- [ ] **Step 5: Commit**

```bash
git add client/lib/widgets/avatar_widget.dart client/test/avatar_widget_test.dart
git commit -m "feat(avatar): rebuild as Iron Man 2 arc-reactor HUD"
```

---

### Task 3: Restyle Home screen chrome

**Files:**
- Modify: `client/lib/screens/home_screen.dart`

**Interfaces:**
- Consumes: `AppTheme` tokens (Task 1); unchanged `AvatarWidget` (Task 2).
- Produces: Home screen with themed status bar, panels, background glow. No new widget API.

- [ ] **Step 1: Add theme import and alias the color constants**

Replace lines 1–17 (imports + const block). Add `import '../utils/theme.dart';` and replace the local const definitions so all existing usage sites keep working:

```dart
const _bg = AppTheme.bg;
const _panel = AppTheme.panel;
const _hud = AppTheme.hud;
const _hudDim = AppTheme.hudDim;
const _text = AppTheme.text;
const _textDim = AppTheme.textDim;
const _danger = AppTheme.accentAmber;
const _success = AppTheme.accentGreen;
```

Delete the old `const _bg = Color(0xFF080818);` … block.

- [ ] **Step 2: Add a faint cyan radial glow behind the avatar**

In `_buildAvatarSection()`, wrap the `AspectRatio` in a `Stack` with a background radial gradient:

```dart
Widget _buildAvatarSection() {
  return Padding(
    padding: EdgeInsets.symmetric(horizontal: 16),
    child: AspectRatio(
      aspectRatio: 1,
      child: Stack(
        alignment: Alignment.center,
        children: [
          DecoratedBox(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: [
                  AppTheme.hud.withValues(alpha: 0.08),
                  AppTheme.hud.withValues(alpha: 0.0),
                ],
              ),
            ),
          ),
          AvatarWidget(
            currentState: _avatarState,
            wordPulse: _wordPulse,
          ),
        ],
      ),
    ),
  );
}
```

- [ ] **Step 3: Run tests + analyze**

Run: `C:\flutter\bin\flutter.bat test`
Expected: existing `widget_test.dart` smoke test still passes (pumps `JarvisApp` → MainScreen).

Run: `C:\flutter\bin\flutter.bat analyze`
Expected: no new errors; pre-existing warnings (unused `_hudDim`/`_lastMessage`/`_transcription`) may remain.

- [ ] **Step 4: Commit**

```bash
git add client/lib/screens/home_screen.dart
git commit -m "feat(home): apply JARVIS theme to home screen"
```

---

### Task 4: Token-swap const-block screens

**Files:**
- Modify: `client/lib/main.dart`
- Modify: `client/lib/screens/main_screen.dart`
- Modify: `client/lib/screens/health_screen.dart`
- Modify: `client/lib/screens/onboarding_screen.dart`
- Modify: `client/lib/screens/specs_check_screen.dart`

**Interfaces:**
- Consumes: `AppTheme` tokens (Task 1).
- Produces: identical layout/navigation, themed colors.

- [ ] **Step 1: Add theme import to each file**

`lib/main.dart` → `import 'utils/theme.dart';`
Each screen → `import '../utils/theme.dart';`

- [ ] **Step 2: Replace const blocks with AppTheme aliases**

For `main.dart`, `main_screen.dart`, `health_screen.dart` (and the shared full block used by `home_screen.dart` already done in Task 3):

| old literal | alias |
|---|---|
| `Color(0xFF080818)` | `AppTheme.bg` |
| `Color(0xFF10102a)` | `AppTheme.panel` |
| `Color(0xFF00e5ff)` | `AppTheme.hud` |
| `Color(0xFF0077b6)` | `AppTheme.hudDim` |
| `Color(0xFFE0E0E0)` | `AppTheme.text` |
| `Color(0xFF6e7681)` | `AppTheme.textDim` |
| `Color(0xFFFF6D00)` | `AppTheme.accentAmber` |
| `Color(0xFF00C853)` | `AppTheme.accentGreen` |

Keep the local const names (`_bg`, `_panel`, `_hud`, …) but assign them the token value, e.g. `const _bg = AppTheme.bg;`. Do NOT rename usages.

For `onboarding_screen.dart` and `specs_check_screen.dart`:

| old literal | alias |
|---|---|
| `Color(0xFF06080d)` (`_void`) | `AppTheme.bg` |
| `Color(0xFF00e5ff)` (`_hud`) | `AppTheme.hud` |
| `Color(0xFF0d1117)` (`_panel`) | `AppTheme.panel` |
| `Color(0xFFc9d1d9)` (`_text`) | `AppTheme.text` |
| `Color(0xFF6e7681)` (`_textDim`) | `AppTheme.textDim` |
| `Color(0xFF3fb950)` (`_success`) | `AppTheme.accentGreen` |
| `Color(0xFFf85149)` (`_danger`) | `AppTheme.accentRed` |

Note: `onboarding_screen.dart` line ~502 uses `Color(0x0800e5ff)` (alpha 0x08) — replace with `AppTheme.hud.withValues(alpha: 0.08)`.

- [ ] **Step 3: Run tests + analyze**

Run: `C:\flutter\bin\flutter.bat test`
Expected: smoke test passes.

Run: `C:\flutter\bin\flutter.bat analyze`
Expected: no new errors or new warnings (pre-existing unused-const warnings may persist).

- [ ] **Step 4: Commit**

```bash
git add client/lib/main.dart client/lib/screens/main_screen.dart client/lib/screens/health_screen.dart client/lib/screens/onboarding_screen.dart client/lib/screens/specs_check_screen.dart
git commit -m "feat(theme): token-swap const-block screens"
```

---

### Task 5: Token-swap inline-literal screens

**Files:**
- Modify: `client/lib/screens/monitoring_screen.dart`
- Modify: `client/lib/screens/devices_screen.dart`
- Modify: `client/lib/screens/camera_screen.dart`
- Modify: `client/lib/screens/browser_screen.dart`
- Modify: `client/lib/screens/screen_share_screen.dart`
- Modify: `client/lib/screens/settings_screen.dart`
- Modify: `client/lib/screens/personality_screen.dart`
- Modify: `client/lib/overlay/overlay_widget.dart`
- Modify: `client/lib/widgets/device_card.dart`
- Modify: `client/lib/widgets/compact_avatar_widget.dart`

**Interfaces:**
- Consumes: `AppTheme` tokens (Task 1).
- Produces: identical layout, themed colors.

- [ ] **Step 1: Add theme import + local aliases to each file**

Add `import '../utils/theme.dart';` (from `lib/screens`, `lib/widgets`, `lib/overlay`).

At the top of each file (after imports), add aliases — only those actually needed:

```dart
const _bg = AppTheme.bg;       // replaces Color(0xFF0a0a1a)
const _panel = AppTheme.panel; // replaces Color(0xFF1a1a2e)
const _hud = AppTheme.hud;     // replaces Color(0xFF00e5ff)
const _text = AppTheme.text;   // replaces Color(0xFFc9d1d9) where present
const _textDim = AppTheme.textDim; // replaces Color(0xFF6e7681) where present
const _success = AppTheme.accentGreen; // replaces Color(0xFF3fb950) where present
const _danger = AppTheme.accentRed;    // replaces Color(0xFFf85149) where present
```

- [ ] **Step 2: Replace inline literals with aliases**

Per-file literal replacements (find → replace, all occurrences):

| literal | replace with |
|---|---|
| `Color(0xFF0a0a1a)` | `_bg` |
| `Color(0xFF1a1a2e)` | `_panel` |
| `Color(0xFF00e5ff)` | `_hud` |
| `Color(0xFF0d1117)` | `_panel` (overlay menus) |
| `Color(0xFFc9d1d9)` | `_text` |
| `Color(0xFF6e7681)` | `_textDim` |
| `Color(0xFF3fb950)` | `_success` |
| `Color(0xFFf85149)` | `_danger` |

Apply only to `*.dart` files listed in this task. Preserve `.withValues(alpha: ...)` chains — replace just the `Color(...)` part.

- [ ] **Step 3: Update compact avatar to use the shared phase colors**

In `client/lib/widgets/compact_avatar_widget.dart`, replace the `_color` getter body with `Color get _color => AppTheme.phaseColor(state);` and delete the hardcoded switch. Keep `_speed` as-is.

- [ ] **Step 4: Run tests + analyze**

Run: `C:\flutter\bin\flutter.bat test`
Expected: smoke test passes.

Run: `C:\flutter\bin\flutter.bat analyze`
Expected: no new errors or new warnings.

- [ ] **Step 5: Commit**

```bash
git add client/lib/screens/monitoring_screen.dart client/lib/screens/devices_screen.dart client/lib/screens/camera_screen.dart client/lib/screens/browser_screen.dart client/lib/screens/screen_share_screen.dart client/lib/screens/settings_screen.dart client/lib/screens/personality_screen.dart client/lib/overlay/overlay_widget.dart client/lib/widgets/device_card.dart client/lib/widgets/compact_avatar_widget.dart
git commit -m "feat(theme): token-swap inline-literal screens"
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

- [ ] **Step 3: Visual check of all five avatar phases**

Run the app (`C:\flutter\bin\flutter.bat run -d windows` or launch via existing workflow). Trigger each phase (idle on launch; speaking via a chat/voice response; listening/thinking during a voice session; error optionally) and confirm:
- avatar shows the arc-reactor core + orbiting particles + segmented rings
- each phase uses its own color (cyan / green / amber / white / red)
- the Home screen shows the cyan radial glow behind the avatar
- other screens are consistently themed (no leftover raw `0x`-style cyan/panel colors that look out of place)

- [ ] **Step 4: Update knowledge graph**

Run: `& "C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\graphify.exe" update .`
Expected: graph rebuilt.

- [ ] **Step 5: Commit any leftovers**

```bash
git add -A
git commit -m "chore: finalize JARVIS avatar redesign"
```
(Only if there are uncommitted changes from the visual-check fixes.)
