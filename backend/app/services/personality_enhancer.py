import random
from typing import Optional


class PersonalityEnhancer:
    def __init__(self):
        self._formality = 0.7
        self._quip_frequency = 0.3
        self._enabled = True

        self._greetings = [
            "At your service.",
            "How may I assist you today?",
            "Ready and waiting.",
            "All systems nominal.",
            "Good to see you, sir.",
        ]

        self._status_quips = [
            "All systems operational.",
            "Running like a Swiss watch.",
            "Smooth as silk.",
            "Everything is in order.",
            "Tip-top condition.",
            "Functioning within normal parameters.",
        ]

        self._error_quips = [
            "That's... not quite right.",
            "I'm afraid that didn't work as expected.",
            "A minor hiccup, nothing serious.",
            "We seem to have hit a small snag.",
            "Apologies, that didn't go as planned.",
        ]

        self._success_quips = [
            "Done and dusted.",
            "Consider it handled.",
            "Mission accomplished.",
            "As you wish.",
            "Completed with my usual precision.",
            "Another task conquered.",
        ]

        self._thinking_quips = [
            "Processing...",
            "One moment, sir.",
            "Let me see what I can do.",
            "Consulting the relevant data.",
            "Running the calculations.",
        ]

        self._code_quips = [
            "Interesting code, sir.",
            "Bold choice of variable names.",
            "This code has character.",
            "I see someone's been busy.",
            "Quite the elegant solution.",
        ]

        self._wellness_quips = [
            "Perhaps a brief respite is in order.",
            "Even machines need rest — and you're not a machine.",
            "A well-deserved break, I'd say.",
            "Shall I dim the lights for a moment?",
        ]

        self._weather_quips = [
            "The sky seems to have opinions today.",
            "Weather's being rather dramatic.",
            "Nature's showing off again.",
        ]

        self._system_quips = [
            "Your hardware is behaving itself.",
            "The silicon is content.",
            "All circuits are happy.",
        ]

    def set_formality(self, value: float):
        self._formality = max(0.0, min(1.0, value))

    def set_quip_frequency(self, value: float):
        self._quip_frequency = max(0.0, min(1.0, value))

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def get_config(self) -> dict:
        return {
            "formality": self._formality,
            "quip_frequency": self._quip_frequency,
            "enabled": self._enabled,
        }

    def enhance_response(self, text: str, context: str = "") -> str:
        if not self._enabled or not text:
            return text

        if self._formality > 0.8:
            text = self._make_formal(text)
        elif self._formality < 0.3:
            text = self._make_casual(text)

        if random.random() < self._quip_frequency:
            quip = self._get_contextual_quip(context, text)
            if quip:
                text = f"{text} {quip}"

        return text

    def _make_formal(self, text: str) -> str:
        replacements = {
            "okay": "very well",
            "ok": "understood",
            "sure": "certainly",
            "got it": "understood",
            "no problem": "my pleasure",
            "yep": "indeed",
            "nope": "I'm afraid not",
        }
        lower = text.lower()
        for casual, formal in replacements.items():
            if casual in lower:
                text = text.replace(casual, formal)
        return text

    def _make_casual(self, text: str) -> str:
        replacements = {
            "certainly": "sure",
            "very well": "okay",
            "understood": "got it",
            "I shall": "I'll",
            "I will": "I'll",
            "would you like me to": "want me to",
        }
        for formal, casual in replacements.items():
            text = text.replace(formal, casual)
        return text

    def _get_contextual_quip(self, context: str, text: str) -> Optional[str]:
        if context == "error" or "error" in text.lower():
            return random.choice(self._error_quips)
        elif context == "success" or any(w in text.lower() for w in ["done", "completed", "success"]):
            return random.choice(self._success_quips)
        elif context == "thinking" or "processing" in text.lower():
            return random.choice(self._thinking_quips)
        elif context == "code" or "code" in text.lower() or "program" in text.lower():
            return random.choice(self._code_quips)
        elif context == "wellness" or "break" in text.lower():
            return random.choice(self._wellness_quips)
        elif context == "weather" or "weather" in text.lower():
            return random.choice(self._weather_quips)
        elif context == "system" or "system" in text.lower():
            return random.choice(self._system_quips)
        elif context == "status":
            return random.choice(self._status_quips)
        return None

    def get_greeting(self) -> str:
        return random.choice(self._greetings)

    def get_status_quip(self) -> str:
        return random.choice(self._status_quips)


personality_enhancer = PersonalityEnhancer()
