import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path


class RoutineStep:
    def __init__(self, action: str, params: Optional[dict] = None, delay: float = 0):
        self.action = action
        self.params = params or {}
        self.delay = delay

    def to_dict(self):
        return {"action": self.action, "params": self.params, "delay": self.delay}

    @classmethod
    def from_dict(cls, data: dict) -> "RoutineStep":
        return cls(
            action=data.get("action", ""),
            params=data.get("params", {}),
            delay=data.get("delay", 0),
        )


class Routine:
    def __init__(self, name: str, description: str = "", steps: Optional[list[RoutineStep]] = None,
                 builtin: bool = False, trigger_phrase: str = ""):
        self.name = name
        self.description = description
        self.steps = steps or []
        self.builtin = builtin
        self.trigger_phrase = trigger_phrase

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "builtin": self.builtin,
            "trigger_phrase": self.trigger_phrase,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Routine":
        steps = [RoutineStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=steps,
            builtin=data.get("builtin", False),
            trigger_phrase=data.get("trigger_phrase", ""),
        )


class RoutineService:
    def __init__(self):
        self._routines: dict[str, Routine] = {}
        self._data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        self._data_file = os.path.join(self._data_dir, "routines.json")
        self._running: Optional[str] = None
        self._progress_callback = None

        self._register_builtins()

    def _register_builtins(self):
        self._routines["good_night"] = Routine(
            name="good_night",
            description="Lock PC, dim lights, set do-not-disturb",
            builtin=True,
            trigger_phrase="good night",
            steps=[
                RoutineStep("lock_pc"),
                RoutineStep("set_volume", {"level": 10}),
                RoutineStep("run_command", {"command": "powershell -Command \"(Get-Process | Where-Object {$_.MainWindowTitle -ne ''}) | ForEach-Object { $_.CloseMainWindow() | Out-Null }\""}),
            ],
        )

        self._routines["leaving"] = Routine(
            name="leaving",
            description="Shutdown services, lock PC, turn off lights",
            builtin=True,
            trigger_phrase="i'm leaving",
            steps=[
                RoutineStep("lock_pc"),
                RoutineStep("set_volume", {"level": 0}),
                RoutineStep("run_command", {"command": "taskkill /F /IM chrome.exe 2>nul"}),
            ],
        )

        self._routines["work_mode"] = Routine(
            name="work_mode",
            description="Open work apps, set volume, enable focus",
            builtin=True,
            trigger_phrase="work mode",
            steps=[
                RoutineStep("set_volume", {"level": 30}),
                RoutineStep("open_app", {"app": "Code"}),
                RoutineStep("open_browser"),
            ],
        )

        self._routines["movie_time"] = Routine(
            name="movie_time",
            description="Dim lights, open media, set volume",
            builtin=True,
            trigger_phrase="movie time",
            steps=[
                RoutineStep("set_volume", {"level": 50}),
                RoutineStep("open_browser"),
            ],
        )

    def _load_custom(self):
        try:
            with open(self._data_file, "r") as f:
                data = json.load(f)
            for name, routine_data in data.items():
                if name not in self._routines or not self._routines[name].builtin:
                    self._routines[name] = Routine.from_dict(routine_data)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_custom(self):
        os.makedirs(self._data_dir, exist_ok=True)
        custom = {name: r.to_dict() for name, r in self._routines.items() if not r.builtin}
        with open(self._data_file, "w") as f:
            json.dump(custom, f, indent=2)

    def get_all(self) -> list[dict]:
        self._load_custom()
        return [r.to_dict() for r in self._routines.values()]

    def get(self, name: str) -> Optional[dict]:
        self._load_custom()
        routine = self._routines.get(name)
        return routine.to_dict() if routine else None

    def create(self, name: str, description: str, steps: list[dict], trigger_phrase: str = "") -> dict:
        name = name.lower().strip().replace(" ", "_")
        if name in self._routines and self._routines[name].builtin:
            return {"status": "error", "message": f"Cannot overwrite builtin routine '{name}'"}

        routine_steps = [RoutineStep.from_dict(s) for s in steps]
        self._routines[name] = Routine(
            name=name,
            description=description,
            steps=routine_steps,
            trigger_phrase=trigger_phrase,
        )
        self._save_custom()
        return {"status": "success", "routine": self._routines[name].to_dict()}

    def delete(self, name: str) -> dict:
        if name in self._routines and self._routines[name].builtin:
            return {"status": "error", "message": "Cannot delete builtin routine"}
        if name in self._routines:
            del self._routines[name]
            self._save_custom()
            return {"status": "success", "message": f"Deleted routine '{name}'"}
        return {"status": "error", "message": f"Routine '{name}' not found"}

    def set_progress_callback(self, callback):
        self._progress_callback = callback

    async def run(self, name: str) -> dict:
        self._load_custom()
        routine = self._routines.get(name)
        if not routine:
            return {"status": "error", "message": f"Routine '{name}' not found"}

        if self._running:
            return {"status": "error", "message": f"Routine '{self._running}' is already running"}

        self._running = name
        results = []

        try:
            from app.services.system_command_service import system_command_service as scs
            from app.services.command_registry import command_registry

            for i, step in enumerate(routine.steps):
                if step.delay > 0:
                    await asyncio.sleep(step.delay)

                if self._progress_callback:
                    await self._progress_callback({
                        "routine": name,
                        "step": i + 1,
                        "total": len(routine.steps),
                        "action": step.action,
                    })

                try:
                    handler = command_registry.handlers.get(step.action)
                    if handler:
                        result = await handler(**step.params)
                    else:
                        result = {"status": "error", "message": f"Unknown action: {step.action}"}
                except Exception as e:
                    result = {"status": "error", "message": str(e)}

                results.append({"action": step.action, "result": result})

        finally:
            self._running = None

        return {
            "status": "success",
            "routine": name,
            "results": results,
            "message": f"Routine '{name}' completed",
        }


routine_service = RoutineService()
