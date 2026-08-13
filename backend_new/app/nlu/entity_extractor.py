"""EntityExtractor - deterministic slot filling via regex rules.

Extracts typed entities (device, temperature, time, target, query, path,
etc.) from raw text for a given intent. Fast-path regexes already capture
named groups; this adds coverage for the classifier path.
"""

import re
from typing import Dict

APP_ALIASES = {
    "youtube": "youtube.com",
    "gmail": "mail.google.com",
    "maps": "google.com/maps",
    "spotify": "open.spotify.com",
    "netflix": "netflix.com",
    "settings": "settings",
    "github": "github.com",
    "google": "google.com",
}


def _numbers(text: str) -> list:
    return re.findall(r"\d+", text)


def _time(text: str) -> str:
    m = re.search(r"\b(\d{1,2})(?:\s*[:.]\s*(\d{2}))?\s*(am|pm)?\b", text)
    if m:
        parts = [m.group(1)]
        if m.group(2):
            parts.append(m.group(2))
        if m.group(3):
            parts.append(m.group(3))
        return " ".join(parts)
    return ""


def _url(text: str) -> str:
    m = re.search(r"\b(?:[a-z0-9\-]+\.)+[a-z]{2,}(?:/[^\s]*)?", text, re.IGNORECASE)
    return m.group(0) if m else ""


def _app_target(text: str) -> str:
    for name, target in APP_ALIASES.items():
        if name in text.lower():
            return target
    return ""


def _after(text: str, *markers) -> str:
    lower = text.lower()
    for m in markers:
        idx = lower.find(m)
        if idx != -1:
            return text[idx + len(m):].strip(" .!?")
    return ""


def extract_entities(text: str, intent: str) -> Dict[str, str]:
    """Extract entities for a given intent from raw text."""
    text = text.strip()
    lower = text.lower()
    params: Dict[str, str] = {}

    if intent in ("smart_home_turn_on", "smart_home_turn_off"):
        rest = _after(text, "turn on ", "switch on ", "turn off ", "switch off ")
        if rest:
            params["device"] = rest

    elif intent == "smart_home_set_thermostat":
        nums = _numbers(text)
        if nums:
            params["temperature"] = nums[0]

    elif intent == "scheduler_alarm":
        t = _time(text)
        if t:
            params["time"] = t

    elif intent in ("scheduler_reminder",):
        rest = _after(text, "remind me to ", "remind me that ")
        if rest:
            params["task"] = rest

    elif intent == "browser_navigate":
        target = _app_target(text) or _url(text)
        if not target:
            rest = _after(text, "open ", "go to ", "navigate to ")
            if rest and len(rest.split()) <= 4:
                target = rest
        if target:
            params["target"] = target

    elif intent in ("browser_youtube", "browser_google"):
        rest = _after(text, "search youtube for ", "search the web for ",
                      "play on youtube ", "open youtube and play ")
        if rest:
            params["query"] = rest
        elif intent == "browser_youtube":
            params["target"] = "youtube.com"

    elif intent in ("file_open", "file_find"):
        rest = _after(text, "open file ", "open document ", "find file ", "search files ",
                      "launch ")
        if rest:
            params["path" if intent == "file_open" else "query"] = rest

    elif intent == "set_personality":
        m = re.search(r"\bbe (more|less) ([a-z]+)\b", lower)
        if m:
            params["direction"] = m.group(1)
            params["trait"] = m.group(2)
        else:
            m = re.search(r"\b(?:more|less) ([a-z]+)\b", lower)
            if m:
                params["trait"] = m.group(1)

    return params
