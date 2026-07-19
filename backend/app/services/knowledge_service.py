import json
import os
import re
from datetime import datetime


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
KB_FILE = os.path.join(DATA_DIR, "knowledge_base.json")


class KnowledgeService:
    def __init__(self):
        self._kb = {"entries": [], "facts": {}, "preferences": {}, "patterns": [], "corrections": []}
        self._pending_learn = None
        self._load()

    def _load(self):
        try:
            if os.path.exists(KB_FILE):
                with open(KB_FILE, "r", encoding="utf-8") as f:
                    self._kb = json.load(f)
                if "facts" not in self._kb or isinstance(self._kb["facts"], list):
                    self._kb["facts"] = {}
                if "preferences" not in self._kb or isinstance(self._kb["preferences"], list):
                    self._kb["preferences"] = {}
        except:
            pass

    def _save(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            self._kb["entries"] = self._kb.get("entries", [])[-300:]
            with open(KB_FILE, "w", encoding="utf-8") as f:
                json.dump(self._kb, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[KNOWLEDGE SAVE ERROR] {e}")

    def store(self, category: str, key: str, value: str, source: str = "conversation"):
        if category == "fact":
            self._kb["facts"][key.lower()] = {"value": value, "updated": datetime.now().isoformat(), "source": source}
        elif category == "preference":
            self._kb["preferences"][key.lower()] = {"value": value, "updated": datetime.now().isoformat(), "source": source}
        else:
            self._kb["entries"].append({
                "category": category, "key": key, "value": value,
                "timestamp": datetime.now().isoformat(), "source": source,
            })

    def lookup(self, key: str) -> str:
        key_lower = key.lower()
        if key_lower in self._kb.get("facts", {}):
            return self._kb["facts"][key_lower]["value"]
        if key_lower in self._kb.get("preferences", {}):
            return self._kb["preferences"][key_lower]["value"]
        for entry in reversed(self._kb.get("entries", [])):
            if key_lower in entry.get("key", "").lower() or key_lower in entry.get("value", "").lower():
                return entry["value"]
        return ""

    def get_context_for_llm(self, user_message: str) -> str:
        parts = []
        facts = self._kb.get("facts", {})
        prefs = self._kb.get("preferences", {})
        corrections = self._kb.get("corrections", [])[-5:]

        if facts:
            relevant = []
            msg_lower = user_message.lower()
            for key, val in facts.items():
                if any(word in msg_lower for word in key.split() if len(word) > 2):
                    relevant.append(f"- {key}: {val['value']}")
            if not relevant:
                relevant = [f"- {k}: {v['value']}" for k, v in list(facts.items())[-10:]]
            if relevant:
                parts.append("Known facts:\n" + "\n".join(relevant))

        if prefs:
            relevant = []
            msg_lower = user_message.lower()
            for key, val in prefs.items():
                if any(word in msg_lower for word in key.split() if len(word) > 2):
                    relevant.append(f"- {key}: {val['value']}")
            if not relevant:
                relevant = [f"- {k}: {v['value']}" for k, v in list(prefs.items())[-10:]]
            if relevant:
                parts.append("User preferences:\n" + "\n".join(relevant))

        if corrections:
            recent = [f"- {c.get('wrong', '')} -> {c.get('correct', '')}" for c in corrections[-3:]]
            parts.append("Corrections (use these instead):\n" + "\n".join(recent))

        return "\n\n".join(parts) if parts else ""

    def extract_and_store(self, user_message: str, llm_response: str = "") -> list[str]:
        learned = []
        msg = user_message.strip()

        learned_patterns = [
            (r"(?:my|the|i(?:'ve| have)) (.+?) (?:is|'s| as) (?:called |named )?(.+)", "fact"),
            (r"(?:i (?:like|love|prefer|enjoy|want|need|use)) (.+)", "preference"),
            (r"(?:don't|do not|never) (.+)", "rule"),
            (r"(?:i (?:hate|dislike|can't stand)) (.+)", "preference"),
        ]

        for pattern, category in learned_patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                key = match.group(1).strip() if match.lastindex else match.group(0).strip()
                value = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else match.group(0).strip()
                self.store(category, key, value)
                learned.append(f"{category}: {key} = {value}")

        if any(w in msg.lower() for w in ["is actually", "is really", "is called", "is named", "it's not", "it is not", "i meant", "i mean"]):
            parts = re.split(r"(?:is actually|is really|is called|is named|it's not|it is not|i meant|i mean)\s*", msg, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) == 2:
                wrong = parts[0].strip().rstrip(".,!")
                correct = parts[1].strip().rstrip(".,!")
                self._kb.setdefault("corrections", []).append({
                    "wrong": wrong, "correct": correct,
                    "timestamp": datetime.now().isoformat(),
                })
                self._kb["corrections"] = self._kb["corrections"][-20:]
                self.store("fact", wrong, correct, source="correction")
                learned.append(f"correction: {wrong} -> {correct}")

        if learned:
            self._save()
        return learned

    def get_stats(self) -> dict:
        return {
            "facts": len(self._kb.get("facts", {})),
            "preferences": len(self._kb.get("preferences", {})),
            "entries": len(self._kb.get("entries", [])),
            "corrections": len(self._kb.get("corrections", [])),
            "total": len(self._kb.get("facts", {})) + len(self._kb.get("preferences", {})) + len(self._kb.get("entries", [])),
        }

    def get_all(self) -> dict:
        return self._kb

    def search(self, query: str) -> list[dict]:
        query_lower = query.lower()
        results = []
        for key, val in self._kb.get("facts", {}).items():
            if query_lower in key or query_lower in val.get("value", "").lower():
                results.append({"category": "fact", "key": key, "value": val["value"]})
        for key, val in self._kb.get("preferences", {}).items():
            if query_lower in key or query_lower in val.get("value", "").lower():
                results.append({"category": "preference", "key": key, "value": val["value"]})
        for entry in self._kb.get("entries", []):
            if query_lower in entry.get("key", "").lower() or query_lower in entry.get("value", "").lower():
                results.append(entry)
        return results[-15:]

    def clear(self):
        self._kb = {"entries": [], "facts": {}, "preferences": {}, "patterns": [], "corrections": []}
        self._save()

    def clear_topic(self, topic: str) -> int:
        topic_lower = topic.lower()
        removed = 0
        if topic_lower in self._kb.get("facts", {}):
            del self._kb["facts"][topic_lower]
            removed += 1
        if topic_lower in self._kb.get("preferences", {}):
            del self._kb["preferences"][topic_lower]
            removed += 1
        before = len(self._kb.get("entries", []))
        self._kb["entries"] = [e for e in self._kb.get("entries", []) if topic_lower not in e.get("key", "").lower()]
        removed += before - len(self._kb.get("entries", []))
        self._save()
        return removed


knowledge_service = KnowledgeService()
