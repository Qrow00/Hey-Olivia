"""Personality - JARVIS's emotional sliders.

Sliders (0.0-1.0) per profile: humor, sarcasm, warmth, energy, formality,
curiosity. Persisted through StateStore. They drive:
  - the chat system prompt (trait descriptors),
  - TTS rendering (voice pick + rate/pitch mapping),
  - the no-model fallback response style.
"""

from typing import Any, Dict, Optional

from app.config import DEFAULT_PERSONALITY, PERSONALITY_SLIDERS

_TRAIT_LINES = {
    "humor": "You enjoy playful wit and light jokes when the moment fits.",
    "sarcasm": "You have a dry, deadpan wit. When sarcasm is high you are snarky and teasing.",
    "warmth": "You are warm, caring, and reassuring toward the user.",
    "energy": "High energy: enthusiastic, quick, upbeat. Low energy: calm, relaxed, understated.",
    "formality": "High formality: crisp, professional, precise language. Low formality: casual, friendly.",
    "curiosity": "You ask curious follow-up questions and explore topics with interest.",
}


class Personality:
    """Per-profile emotional slider state with TTS + prompt mapping."""

    def __init__(self, state_store=None, profile: str = "default"):
        self._store = state_store
        self._profile = profile
        self._key = "personality.sliders"
        self._values: Dict[str, float] = dict(DEFAULT_PERSONALITY)
        if self._store is not None:
            stored = self._store.get(profile, self._key, {}) or {}
            for k in PERSONALITY_SLIDERS:
                v = stored.get(k)
                if isinstance(v, (int, float)):
                    self._values[k] = max(0.0, min(1.0, float(v)))

    def sliders(self) -> Dict[str, float]:
        return dict(self._values)

    def set_slider(self, name: str, value: float) -> bool:
        if name not in PERSONALITY_SLIDERS:
            return False
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False
        if not (0.0 <= value <= 1.0):
            return False
        self._values[name] = round(value, 2)
        if self._store is not None:
            self._store.set(self._profile, self._key, self._values)
        return True

    def set_many(self, updates: Dict[str, Any]) -> Dict[str, float]:
        for k, v in updates.items():
            self.set_slider(k, v)
        return self.sliders()

    def adjust(self, trait: str, direction: str, step: float = 0.2) -> bool:
        """'more'/'less' control: e.g. "be more sarcastic"."""
        slider = None
        for k in PERSONALITY_SLIDERS:
            if trait in k or k in trait:
                slider = k
                break
        if slider is None:
            return False
        delta = step if direction == "more" else -step
        new_val = self._values[slider] + delta
        return self.set_slider(slider, new_val)

    # --- rendering ----------------------------------------------------------

    def system_prompt(self) -> str:
        lines = [
            "You are J.A.R.V.I.S., an intelligent, loyal AI assistant.",
            "You speak naturally, concisely, and with character.",
        ]
        for trait in PERSONALITY_SLIDERS:
            v = self._values[trait]
            if v < 0.25:
                continue
            if v >= 0.75:
                lines.append(_TRAIT_LINES[trait].replace("When sarcasm is high",
                                                         "Be noticeably more sarcastic"))
            elif v >= 0.5:
                lines.append(_TRAIT_LINES[trait])
            else:
                lines.append(_TRAIT_LINES[trait].split(".")[0] +
                             f", with {trait} only subtly applied.")
        lines.append("End each reply with substance, never filler.")
        return "\n".join(lines)

    def tts_params(self) -> Dict[str, Any]:
        """Map sliders to edge-tts voice selection + prosody.

        Base voice is the classic JARVIS-style British male (RyanNeural);
        warmth/formality shift toward warmer/older British voices.
        """
        energy = self._values["energy"]
        warmth = self._values["warmth"]
        sarcasm = self._values["sarcasm"]
        formality = self._values["formality"]

        if warmth >= 0.8:
            voice = "en-GB-SoniaNeural"
        elif formality >= 0.7:
            voice = "en-GB-ThomasNeural"
        else:
            voice = "en-GB-RyanNeural"
        return {
            "voice": voice,
            "rate": round(0.92 + energy * 0.3, 2),
            "pitch": round(-0.05 + sarcasm * 0.1, 3),
            "energy": energy,
            "sarcasm": sarcasm,
            "volume": round(1.0 + (energy - 0.5) * 0.15, 3),
        }

    # --- fallback replies (no model loaded) ---------------------------------

    def fallback_replies(self) -> Dict[str, str]:
        """Personality-flavored template responses keyed by intent group."""
        if self._values["sarcasm"] >= 0.6:
            generic = "Oh, fantastic. I would love to do that if I had a model loaded. Try starting me with one."
        elif self._values["formality"] >= 0.7:
            generic = "I would be glad to assist. My conversational model is currently offline, so I cannot elaborate further."
        else:
            generic = "I'm here. My conversation model is offline right now, but I can still run commands."
        return {
            "greeting": "Hello, Tony. At your service.",
            "thanks": "Always a pleasure.",
            "goodbye": "Goodbye. I'll be here if you need me.",
            "joke": "Why did the AI cross the road? To optimize the chicken's path.",
            "info_health": "All systems nominal. Personality sliders engaged.",
            "chat": generic,
        }

    def style_fallback(self, text: str) -> str:
        """Style an arbitrary fallback reply per current sliders."""
        base = f"I understand you said: {text.strip() or '(nothing)'}. "
        if self._values["energy"] >= 0.7:
            base += "On it — fast and efficient!"
        elif self._values["sarcasm"] >= 0.7:
            base += "Thrilling, I know."
        elif self._values["warmth"] >= 0.7:
            base += "Happy to help, always."
        else:
            base += "Let me know if you need anything."
        return base
