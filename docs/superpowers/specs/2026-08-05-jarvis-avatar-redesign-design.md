# Iron Man JARVIS UI — Avatar Redesign + App Theme

**Date:** 2026-08-05
**Status:** Approved (design gate passed)

## Overview

Redesign the JARVIS avatar from a generic HUD circle into an authentic
Iron Man 2-era JARVIS interface: an arc-reactor core with orbiting particle
streams, rotating segmented rings, helmet-style corner brackets, and HUD data
readouts — each voice phase rendered in its own color. Apply the same Iron Man
cyan-on-near-black identity across the whole app via a shared theme token
file.

## Requirements (from brainstorming)

- **Scope:** Avatar widget full redesign + whole-app theme.
- **Style:** Iron Man 2 cyan HUD aesthetic (the look most people picture as
  "JARVIS UI").
- **Phase colors (all five distinct):**
  - idle = cyan `#40F9FF`
  - listening = green `#00FF88`
  - thinking = amber `#FFB300`
  - speaking = white `#FFFFFF`
  - error = red `#FF4444`
- **Home layout:** keep the existing vertical structure (status bar / avatar /
  chat history / input); restyle everything with the theme.
- **Motion:** calm ambient flow at idle, speed/react per phase; respect
  reduced-motion preferences.
- **No new dependencies** — reuse CustomPainter + existing Flutter widgets.

## Section 1 — Avatar (`client/lib/widgets/avatar_widget.dart`)

Rebuild `JarvisHudPainter` from scratch. Keep the existing `AvatarWidget`
state/speed/pulse plumbing and the single `AnimationController` driving
`progress`; replace only the painting + per-state color/speed mapping.

### Composition (300×300 canvas, center 150,150)

1. **Arc-reactor core (center)** — signature element. Bright glowing torus
   ring, cross-spokes, inner white-hot disc, soft radial glow. Pulses slowly;
   swells with `wordPulse` while speaking.
2. **Orbiting particle streams** — 2–3 concentric rings of bright dots flowing
   in opposite directions. Count/speed scale with phase.
3. **Rotating segmented rings** — two thin dashed arcs rotating slowly,
   phase-tinted.
4. **Tick ring** — fine perimeter ticks, a few lit as they pass a read marker.
5. **Corner brackets** — Iron Man helmet HUD brackets inside the circle edges,
   blinking gently.
6. **Data readouts** — small uppercase monospace labels with wide
   letter-spacing: fixed "SYS ONLINE", "ALL SYSTEMS FUNCTIONING", plus a
   phase line (listening → "SCANNING", thinking → "PROCESSING",
   speaking → "VOICE OUTPUT", error → "SYSTEM FAULT").
7. **J.A.R.V.I.S. wordmark** — bottom, in phase tint, with underline.

### Phase behavior

| phase | color | motion |
|---|---|---|
| idle | cyan | slow ~8s drift, calm particles |
| listening | green | scan arc sweeps, particles speed up |
| thinking | amber | rings spin fast, core flickers |
| speaking | white | particles pulse with `wordPulse`, core swells |
| error | red | rings jitter, core strobes |

## Section 2 — App theme (`client/lib/utils/theme.dart`)

New token file replacing duplicated per-screen color constants. Exports
palette + type helpers; no new font dependency (system monospace for data
labels).

### Palette

| token | value | use |
|---|---|---|
| `bg` | `#050810` | screen background |
| `panel` | `#0A0E1A` | cards/panels |
| `panelAlt` | `#121a2e` | raised surfaces |
| `hud` | `#40F9FF` | primary cyan |
| `hudDim` | `#0099CC` | muted cyan |
| `hudGlow` | `#00E5FF` | glow accents |
| `text` | `#E8F6FF` | primary text |
| `textDim` | `#7A8BA8` | secondary text |
| phase accents | green/amber/white/red above | per-phase |

### Screens

- **Home screen:** full restyle — status bar, avatar section, chat history
  panel, input all consume tokens; faint cyan radial glow behind the avatar.
- **All other screens** (Monitoring, Health, Devices, Smart Home, Camera /
  Vision, Screen Share, Personality, Settings, Specs Check, Onboarding): swap
  their duplicated `_bg/_panel/_hud/...` const blocks to shared tokens.
  Cosmetic only — no layout or behavior changes, no refactors beyond the color
  swap.

## Verification

- `flutter analyze` — no new errors or warnings.
- App builds and runs.
- Avatar renders all five phase states with correct colors.
- Screens visually consistent (cyan-on-near-black).

## Out of scope

- No new dependencies.
- No layout/navigation changes.
- No changes to voice, monitoring, or other backend behavior.
