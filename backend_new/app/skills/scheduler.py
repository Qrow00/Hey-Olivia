"""Scheduler skills: reminders and alarms, persisted through StateStore.

Reminders/alarms are stored per profile under `scheduler.items` so they
survive restarts. A background watchdog (see scheduler_watchdog below) fires
due items and broadcasts them over the WebSocket manager.
"""

import asyncio
import datetime
import json
import re
import time
import uuid
from typing import Any, Dict, List, Optional

_STORE_KEY = "scheduler.items"
_FIRED_KEY = "scheduler.fired"


def _profile(ctx: Any) -> str:
    cfg = getattr(ctx, "cfg", None)
    if cfg is not None and getattr(cfg, "profile", None):
        return cfg.profile
    return "default"


def _items(ctx: Any) -> List[Dict[str, Any]]:
    store = getattr(ctx, "state_store", None)
    if store is None:
        return []
    return store.get(_profile(ctx), _STORE_KEY, []) or []


def _save(ctx: Any, items: List[Dict[str, Any]]) -> bool:
    store = getattr(ctx, "state_store", None)
    if store is None:
        return False
    store.set(_profile(ctx), _STORE_KEY, items)
    return True


def _today_alarm_time(when: str) -> Optional[datetime.datetime]:
    """Parse '7:00 AM'/'19:30' into *today's* datetime (no roll-forward)."""
    m = re.search(r"\b(\d{1,2})(?:\s*[:.]\s*(\d{2}))?\s*(am|pm)?\b", (when or "").strip())
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    suffix = (m.group(3) or "").lower()
    if suffix == "pm" and hour < 12:
        hour += 12
    elif suffix == "am" and hour == 12:
        hour = 0
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


def parse_alarm_time(when: str) -> Optional[datetime.datetime]:
    """Return the *next* occurrence of the parsed time (today, else tomorrow)."""
    target = _today_alarm_time(when)
    if target is None:
        return None
    if target <= datetime.datetime.now():
        target += datetime.timedelta(days=1)
    return target


def due_items(ctx: Any, grace_seconds: int = 60) -> List[Dict[str, Any]]:
    """Return unscheduled alarms whose time has arrived (within grace window)."""
    now = datetime.datetime.now()
    store = getattr(ctx, "state_store", None)
    profile = _profile(ctx)
    fired = set(store.get(profile, _FIRED_KEY, []) or []) if store else set()
    due = []
    for item in _items(ctx):
        if item.get("done") or item.get("id") in fired:
            continue
        if item.get("kind") != "alarm" or not item.get("when"):
            continue
        target = _today_alarm_time(item["when"])
        if target is not None and (now - target).total_seconds() <= grace_seconds and target <= now:
            due.append(item)
    return due


async def scheduler_watchdog(ctx: Any, manager: Any, poll_seconds: int = 20) -> None:
    """Background loop: broadcast due alarms, then mark them fired once."""
    store = getattr(ctx, "state_store", None)
    while True:
        try:
            for item in due_items(ctx):
                await manager.broadcast({
                    "type": "reminder_due",
                    "kind": item.get("kind"),
                    "when": item.get("when"),
                    "id": item.get("id"),
                })
                if store is not None:
                    profile = _profile(ctx)
                    fired = list(store.get(profile, _FIRED_KEY, []) or [])
                    fired.append(item.get("id"))
                    store.set(profile, _FIRED_KEY, fired)
                    items = _items(ctx)
                    for i in items:
                        if i.get("id") == item.get("id"):
                            i["done"] = True
                    _save(ctx, items)
        except Exception as e:
            print(f"[Scheduler] watchdog error: {e}")
        await asyncio.sleep(poll_seconds)


async def scheduler_reminder(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    task = (params.get("task") or "").strip()
    if not task:
        return {"success": False, "narration": "Remind me to do what?",
                "type": "scheduler_result"}
    items = _items(ctx)
    items.append({"id": str(uuid.uuid4())[:8], "kind": "reminder", "task": task,
                  "when": params.get("when", ""), "created": time.time(),
                  "done": False})
    if not _save(ctx, items):
        return {"success": False, "narration": "Scheduler storage unavailable.",
                "type": "scheduler_result"}
    return {"success": True,
            "narration": f"Reminder set: {task}.",
            "type": "scheduler_result", "data": {"count": len(items)}}


async def scheduler_alarm(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    when = (params.get("time") or "").strip()
    if not when:
        return {"success": False, "narration": "Alarm for when?",
                "type": "scheduler_result"}
    items = _items(ctx)
    items.append({"id": str(uuid.uuid4())[:8], "kind": "alarm", "task": "alarm",
                  "when": when, "created": time.time(), "done": False})
    if not _save(ctx, items):
        return {"success": False, "narration": "Scheduler storage unavailable.",
                "type": "scheduler_result"}
    return {"success": True,
            "narration": f"Alarm set for {when}.",
            "type": "scheduler_result", "data": {"count": len(items)}}


def register(reg) -> None:
    reg.skill("scheduler_reminder", scheduler_reminder,
              description="Set a reminder (params: task, when)")
    reg.skill("scheduler_alarm", scheduler_alarm,
              description="Set an alarm (params: time)")
