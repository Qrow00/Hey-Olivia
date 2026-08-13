"""Fast-path regex patterns mapping utterances to intents.

Checked first (< 10ms). If a pattern matches with named capture groups,
entities are extracted without any model. Everything else falls through
to the intent classifier.
"""

import re
from typing import Dict, List, Optional

# intent -> list of (regex, named-entity-map)
_PATTERNS: Dict[str, List[Dict]] = {}

# Alias map: common "sayings" -> canonical entity values.
APP_ALIASES = {
    "youtube": "youtube.com",
    "gmail": "mail.google.com",
    "gmail inbox": "mail.google.com/mail/#inbox",
    "maps": "google.com/maps",
    "spotify": "open.spotify.com",
    "netflix": "netflix.com",
    "chrome": "chrome",
    "settings": "settings",
}


def _pat(intent: str, regex: str, entities: Optional[Dict[str, str]] = None):
    _PATTERNS.setdefault(intent, []).append(
        {"re": re.compile(regex, re.IGNORECASE), "entities": entities or {}}
    )


# --- system ----------------------------------------------------------------
_pat("system_shutdown", r"\b(shutdown|turn off (the )?(computer|pc)|power off|switch off)\b")
_pat("system_restart", r"\b(restart|reboot)\b")
_pat("system_sleep", r"\b(sleep( mode)?|hibernate|go to sleep)\b")
_pat("system_volume_up", r"\b(volume up|increase volume|turn (the )?volume up|louder)\b", {"amount": "up"})
_pat("system_volume_down", r"\b(volume down|decrease volume|turn (the )?volume down|quieter)\b", {"amount": "down"})
_pat("system_brightness_up", r"\b(brightness up|increase brightness)\b", {"amount": "up"})
_pat("system_brightness_down", r"\b(brightness down|decrease brightness)\b", {"amount": "down"})
_pat("system_lock", r"\b(lock (the )?(computer|screen|pc))\b")
_pat("system_mute", r"\b(mute|unmute)\b")

# --- info ------------------------------------------------------------------
_pat("info_time", r"\b(what time is it|tell me the time|what'?s the time|time please)\b")
_pat("info_date", r"\b(what('s| is) (the )?date|today('s| is what) date|tell me (the )?date)\b")
_pat("info_weather", r"\b(weather|temperature outside|how cold|how hot)\b")
_pat("info_uptime", r"\b(how long (has|have|has the) (the )?(system|pc|computer) (been )?on|system uptime)\b")
_pat("info_health", r"\b(how are you|are you ok|how are things|what's up|status)\b")

# --- smart home ------------------------------------------------------------
_pat("smart_home_turn_on", r"\b(?:turn|switch) on(?: the)? ([a-z ]+)\b", {"device": "1"})
_pat("smart_home_turn_off", r"\b(?:turn|switch) off(?: the)? ([a-z ]+)\b", {"device": "1"})
_pat("smart_home_lock_door", r"\b(?:lock (?:the )?door)\b")
_pat("smart_home_set_thermostat", r"\bset (?:the )?(?:thermostat|temperature) to (\d+)\b", {"temperature": "1"})

# --- media -----------------------------------------------------------------
_pat("media_play", r"\b(play|start)\b")
_pat("media_pause", r"\b(pause|freeze)\b")
_pat("media_next", r"\b(next|skip|forward)\b")
_pat("media_previous", r"\b(previous|back|rewind)\b")
_pat("media_stop", r"\b(stop (the )?(media|music|video)?)\b")

# --- browser / web ---------------------------------------------------------
_pat("browser_navigate", r"\b(open|go to|navigate to)\s+([a-z0-9\-\.]+\.[a-z]{2,}|[a-z ]+)\b", {"target": "2"})
_pat("browser_youtube", r"\b(?:search youtube(?: for)?|play on youtube|open youtube)\s*(.*)\b", {"query": "1"})
_pat("browser_google", r"\b(?:search (?:the web|google) for |google)\s*(.*)\b", {"query": "1"})
_pat("browser_youtube_open", r"\b(open|go to) youtube\b", {"target": "youtube.com"})

# --- files / docs ----------------------------------------------------------
_pat("file_open", r"\b(?:open file|open document|launch)\s+(.*)\b", {"path": "1"})
_pat("file_find", r"\b(find file|search files|locate)\s+(.*)\b", {"query": "1"})
_pat("file_list", r"\b(list files|show files|what files)\b")
_pat("docs_new", r"\b(create|make|new|start)\s+(a\s+)?(word document|doc|document|text file)\b", {"kind": "word"})
_pat("docs_edit", r"\b(edit|open)\s+(the\s+)?(word document|doc)\b", {"kind": "word"})

# --- email -----------------------------------------------------------------
_pat("email_read", r"\b(read (my )?email(s)?|check (my )?email|new email(s)?|inbox)\b")
_pat("email_write", r"\b(write|compose|send)\s+(an? )?email\b")
_pat("email_summarize", r"\b(summarize (my )?email(s)?|email summary)\b")

# --- camera / cctv ---------------------------------------------------------
_pat("camera_capture", r"\b(take a picture|take a photo|capture (a )?(photo|image)|use (the )?camera)\b")
_pat("cctv_view", r"\b(show (the )?cctv|cctv feed|security cameras?|view cameras?)\b")
_pat("cctv_analyze", r"\b(analyze|check|monitor)\s+(the\s+)?(cctv|camera feed|security feed)\b")
_pat("vision_identify", r"\b(who is (this|that|he|she)|identify (this )?person|recognize (this )?face)\b")

# --- mobile ----------------------------------------------------------------
_pat("adb_devices", r"\b(list (my )?devices|connected devices|show (my )?phones?)\b")
_pat("adb_screen", r"\b(screenshot (the )?(phone|device))\b", {"action": "screenshot"})

# --- scheduler / reminders -------------------------------------------------
_pat("scheduler_reminder", r"\b(?:remind me to)\s+(.*)\b", {"task": "1"})
_pat("scheduler_alarm", r"\bset (?:an? )?alarm (?:for|at)\s*(.*)\b", {"time": "1"})

# --- code ------------------------------------------------------------------
_pat("code_scaffold", r"\b(?:scaffold|create|make)\s+(?:a\s+)?(python|flutter|web|node)\s+(?:app|project)\b", {"language": "1"})

# --- personality -----------------------------------------------------------
_pat("set_personality", r"\bbe (?:more|less) ([a-z]+)\b", {"trait": "1"})

# --- teach / learn ---------------------------------------------------------
_pat("teach_skill", r"\b(teach (you|jarvis)|learn this|i'?ll show you)\b")

# --- fallbacks -------------------------------------------------------------
_pat("greeting", r"\b(hello|hi|hey|good (morning|afternoon|evening)|yo)\b")
_pat("thanks", r"\b(thank(s| you)|thanks a lot|appreciate (it|that))\b")
_pat("goodbye", r"\b(bye|goodbye|see you|good night)\b")
_pat("joke", r"\b(tell me a joke|make me laugh|another joke)\b")


def match_fast(text: str) -> Optional[Dict[str, object]]:
    """Return {intent, params, confidence} for a fast-path regex match or None."""
    lower = text.lower().strip()
    if not lower:
        return None
    for intent, rules in _PATTERNS.items():
        for rule in rules:
            m = rule["re"].search(lower)
            if m:
                params = {}
                for key, group_idx in rule["entities"].items():
                    g = m.group(int(group_idx)) if m.lastindex and int(group_idx) <= m.lastindex else None
                    if g:
                        params[key] = g.strip()
                # Named capture groups (Python < 3.14 uses groupdict)
                for k, v in m.groupdict().items():
                    if v is not None:
                        params[k] = v.strip()
                return {"intent": intent, "params": params, "confidence": 0.99}
    return None
