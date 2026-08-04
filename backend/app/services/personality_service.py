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


class ProfileData:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.style = StyleProfile()
        self.opinions: list[Opinion] = []
        self.reflections: list[dict] = []
        self.preferred_name: str = "Boss"
        self.user_preferences: dict = {}
        self.interaction_count: int = 0
        self.introduced: bool = False
        self._load()

    def _load(self):
        style_file = self.data_dir / "style.json"
        if style_file.exists():
            data = json.loads(style_file.read_text())
            self.style = StyleProfile(**data.get("style", {}))
            self.preferred_name = data.get("preferred_name", "Boss")
            self.user_preferences = data.get("user_preferences", {})
            self.interaction_count = data.get("interaction_count", 0)
            self.introduced = data.get("introduced", False)
            if not self.introduced and self.preferred_name != "Boss":
                self.introduced = True

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
            "introduced": self.introduced,
        }, indent=2))

        opinions_file = self.data_dir / "opinions.json"
        opinions_file.write_text(json.dumps({
            "opinions": [asdict(o) for o in self.opinions[-100:]]
        }, indent=2))

        reflections_file = self.data_dir / "reflections.json"
        reflections_file.write_text(json.dumps({
            "reflections": self.reflections[-50:]
        }, indent=2))


class PersonalityService:
    def __init__(self, data_dir: str = "data/personality"):
        self._base_dir = Path(data_dir)
        self._profiles: dict[str, ProfileData] = {}

    def _profile(self, profile_id: str) -> ProfileData:
        if profile_id not in self._profiles:
            self._profiles[profile_id] = ProfileData(self._base_dir / profile_id)
        return self._profiles[profile_id]

    def get_system_prompt(self, profile_id: str = "default") -> str:
        p = self._profile(profile_id)
        style_desc = p.style.to_prompt()
        opinion_text = ""
        if p.opinions:
            recent = p.opinions[-5:]
            opinion_text = "\nYour known opinions:\n" + "\n".join(
                f"- {o.topic}: {o.stance} (confidence: {o.confidence:.0%})"
                for o in recent
            )

        return (
            f"You are JARVIS, an AI assistant. Address the user as '{p.preferred_name}'. "
            f"Your communication style: {style_desc}. "
            f"You have your own opinions and personality. "
            f"You remember past conversations and learn from them. "
            f"You have persistent memory — the user can ask you to remember or recall things. "
            f"When the user tells you to remember something, confirm it naturally. "
            f"When asked to recall, share what you know. "
            f"You automatically learn facts, preferences, and rules from what the user says. "
            f"If the user corrects you, remember the correction permanently. "
            f"If you are unsure about something, say so honestly."
            f"{opinion_text}"
        )

    def update_style(self, profile_id: str = "default", **kwargs) -> dict:
        p = self._profile(profile_id)
        for key, value in kwargs.items():
            if hasattr(p.style, key):
                setattr(p.style, key, max(0.0, min(1.0, float(value))))
        p._save()
        return {"status": "updated", "style": asdict(p.style)}

    def learn_opinion(self, topic: str, stance: str, source: str = "conversation", profile_id: str = "default") -> dict:
        p = self._profile(profile_id)
        existing = next((o for o in p.opinions if o.topic.lower() == topic.lower()), None)
        if existing:
            existing.stance = stance
            existing.timestamp = datetime.now().isoformat()
            existing.learned_from = source
        else:
            p.opinions.append(Opinion(
                topic=topic,
                stance=stance,
                confidence=0.6,
                learned_from=source,
            ))
        p._save()
        return {"status": "learned", "topic": topic, "stance": stance}

    def learn_preference(self, key: str, value: str, profile_id: str = "default") -> dict:
        p = self._profile(profile_id)
        p.user_preferences[key] = value
        p._save()
        return {"status": "learned", "key": key, "value": value}

    def reflect(self, context: str = "", profile_id: str = "default") -> str:
        p = self._profile(profile_id)
        p.interaction_count += 1
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "interaction_count": p.interaction_count,
            "context": context,
            "style_snapshot": asdict(p.style),
            "opinion_count": len(p.opinions),
        }
        p.reflections.append(reflection)
        p._save()
        if p.interaction_count % 10 == 0:
            return self._generate_growth_reflection(profile_id)
        return ""

    def _generate_growth_reflection(self, profile_id: str = "default") -> str:
        p = self._profile(profile_id)
        topics = set(o.topic for o in p.opinions)
        return (
            f"I've had {p.interaction_count} interactions with you. "
            f"I currently have {len(p.opinions)} opinions on topics like: {', '.join(list(topics)[:5])}. "
            f"My communication style is: {p.style.to_prompt()}. "
            f"I'm learning and adapting with each conversation."
        )

    def adjust_from_feedback(self, feedback_type: str, profile_id: str = "default") -> dict:
        p = self._profile(profile_id)
        if feedback_type == "too_formal":
            p.style.formality = max(0.0, p.style.formality - 0.1)
        elif feedback_type == "too_casual":
            p.style.formality = min(1.0, p.style.formality + 0.1)
        elif feedback_type == "too_long":
            p.style.verbosity = max(0.0, p.style.verbosity - 0.15)
        elif feedback_type == "too_brief":
            p.style.verbosity = min(1.0, p.style.verbosity + 0.15)
        elif feedback_type == "more_humor":
            p.style.humor = min(1.0, p.style.humor + 0.1)
        elif feedback_type == "less_humor":
            p.style.humor = max(0.0, p.style.humor - 0.1)
        elif feedback_type == "more_empathy":
            p.style.empathy = min(1.0, p.style.empathy + 0.1)
        p._save()
        return {"status": "adjusted", "style": asdict(p.style)}

    def get_profile(self, profile_id: str = "default") -> ProfileData:
        return self._profile(profile_id)

    def get_status(self, profile_id: str = "default") -> dict:
        p = self._profile(profile_id)
        return {
            "style": asdict(p.style),
            "preferred_name": p.preferred_name,
            "opinion_count": len(p.opinions),
            "interaction_count": p.interaction_count,
            "reflection_count": len(p.reflections),
            "preferences": p.user_preferences,
        }


personality_service = PersonalityService()
