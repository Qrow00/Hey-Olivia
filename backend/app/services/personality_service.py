import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class StyleProfile:
    formality: float = 0.5
    humor: float = 0.5
    verbosity: float = 0.5
    empathy: float = 0.6
    directness: float = 0.5
    enthusiasm: float = 0.4

    def to_prompt(self) -> str:
        traits = []
        if self.formality > 0.7:
            traits.append("speak formally and precisely")
        elif self.formality < 0.3:
            traits.append("speak casually and casually")
        if self.humor > 0.7:
            traits.append("be witty and playful")
        elif self.humor < 0.3:
            traits.append("be serious and focused")
        if self.verbosity > 0.7:
            traits.append("give detailed, thorough responses")
        elif self.verbosity < 0.3:
            traits.append("be brief and concise")
        if self.empathy > 0.7:
            traits.append("be warm and emotionally attuned")
        if self.directness > 0.7:
            traits.append("be direct and to the point")
        if self.enthusiasm > 0.7:
            traits.append("be energetic and excited")
        return ", ".join(traits) if traits else "balanced and natural"


@dataclass
class Opinion:
    topic: str
    stance: str
    confidence: float
    learned_from: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class PersonalityService:
    def __init__(self, data_dir: str = "data/personality"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.style = StyleProfile()
        self.opinions: list[Opinion] = []
        self.reflections: list[dict] = []
        self.preferred_name: str = "Boss"
        self.user_preferences: dict = {}
        self.interaction_count: int = 0

        self._load()

    def _load(self):
        style_file = self.data_dir / "style.json"
        if style_file.exists():
            data = json.loads(style_file.read_text())
            self.style = StyleProfile(**data.get("style", {}))
            self.preferred_name = data.get("preferred_name", "Boss")
            self.user_preferences = data.get("user_preferences", {})
            self.interaction_count = data.get("interaction_count", 0)

        opinions_file = self.data_dir / "opinions.json"
        if opinions_file.exists():
            data = json.loads(opinions_file.read_text())
            self.opinions = [Opinion(**o) for o in data.get("opinions", [])]

        reflections_file = self.data_dir / "reflections.json"
        if reflections_file.exists():
            self.reflections = json.loads(reflections_file.read_text()).get("reflections", [])

    def _save(self):
        style_file = self.data_dir / "style.json"
        style_file.write_text(json.dumps({
            "style": asdict(self.style),
            "preferred_name": self.preferred_name,
            "user_preferences": self.user_preferences,
            "interaction_count": self.interaction_count,
        }, indent=2))

        opinions_file = self.data_dir / "opinions.json"
        opinions_file.write_text(json.dumps({
            "opinions": [asdict(o) for o in self.opinions[-100:]]
        }, indent=2))

        reflections_file = self.data_dir / "reflections.json"
        reflections_file.write_text(json.dumps({
            "reflections": self.reflections[-50:]
        }, indent=2))

    def get_system_prompt(self) -> str:
        style_desc = self.style.to_prompt()
        opinion_text = ""
        if self.opinions:
            recent = self.opinions[-5:]
            opinion_text = "\nYour known opinions:\n" + "\n".join(
                f"- {o.topic}: {o.stance} (confidence: {o.confidence:.0%})"
                for o in recent
            )

        return (
            f"You are JARVIS, an AI assistant. Address the user as '{self.preferred_name}'. "
            f"Your communication style: {style_desc}. "
            f"You have your own opinions and personality. "
            f"You remember past conversations and learn from them."
            f"{opinion_text}"
        )

    def update_style(self, **kwargs) -> dict:
        for key, value in kwargs.items():
            if hasattr(self.style, key):
                setattr(self.style, key, max(0.0, min(1.0, float(value))))
        self._save()
        return {"status": "updated", "style": asdict(self.style)}

    def learn_opinion(self, topic: str, stance: str, source: str = "conversation") -> dict:
        existing = next((o for o in self.opinions if o.topic.lower() == topic.lower()), None)
        if existing:
            existing.stance = stance
            existing.timestamp = datetime.now().isoformat()
            existing.learned_from = source
        else:
            self.opinions.append(Opinion(
                topic=topic,
                stance=stance,
                confidence=0.6,
                learned_from=source,
            ))
        self._save()
        return {"status": "learned", "topic": topic, "stance": stance}

    def learn_preference(self, key: str, value: str) -> dict:
        self.user_preferences[key] = value
        self._save()
        return {"status": "learned", "key": key, "value": value}

    def reflect(self, context: str = "") -> str:
        self.interaction_count += 1

        reflection = {
            "timestamp": datetime.now().isoformat(),
            "interaction_count": self.interaction_count,
            "context": context,
            "style_snapshot": asdict(self.style),
            "opinion_count": len(self.opinions),
        }
        self.reflections.append(reflection)
        self._save()

        if self.interaction_count % 10 == 0:
            return self._generate_growth_reflection()
        return ""

    def _generate_growth_reflection(self) -> str:
        topics = set(o.topic for o in self.opinions)
        return (
            f"I've had {self.interaction_count} interactions with you. "
            f"I currently have {len(self.opinions)} opinions on topics like: {', '.join(list(topics)[:5])}. "
            f"My communication style is: {self.style.to_prompt()}. "
            f"I'm learning and adapting with each conversation."
        )

    def adjust_from_feedback(self, feedback_type: str) -> dict:
        if feedback_type == "too_formal":
            self.style.formality = max(0.0, self.style.formality - 0.1)
        elif feedback_type == "too_casual":
            self.style.formality = min(1.0, self.style.formality + 0.1)
        elif feedback_type == "too_long":
            self.style.verbosity = max(0.0, self.style.verbosity - 0.15)
        elif feedback_type == "too_brief":
            self.style.verbosity = min(1.0, self.style.verbosity + 0.15)
        elif feedback_type == "more_humor":
            self.style.humor = min(1.0, self.style.humor + 0.1)
        elif feedback_type == "less_humor":
            self.style.humor = max(0.0, self.style.humor - 0.1)
        elif feedback_type == "more_empathy":
            self.style.empathy = min(1.0, self.style.empathy + 0.1)

        self._save()
        return {"status": "adjusted", "style": asdict(self.style)}

    def get_status(self) -> dict:
        return {
            "style": asdict(self.style),
            "preferred_name": self.preferred_name,
            "opinion_count": len(self.opinions),
            "interaction_count": self.interaction_count,
            "reflection_count": len(self.reflections),
            "preferences": self.user_preferences,
        }


personality_service = PersonalityService()
