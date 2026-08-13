"""SmartHomePlugin - Smart home device control.

Handles command dispatcher output for smart home actions.
In production: integrates with MQTT broker (Tasmota/Shelly devices).
"""

from app.plugins.base import BasePlugin
import asyncio
import json
from typing import Dict, Any, Optional

import psutil


class SmartHomePlugin(BasePlugin):
    """Smart home device control plugin."""

    name = "smart_home"

    def __init__(self):
        super().__init__()
        self.connected = False
        self.device_topics: Dict[str, str] = {}

    async def start(self, kernel) -> None:
        """Initialize smart home plugin."""
        self.connected = True
        print("[SmartHomePlugin] Initialized, ready for device control")

    async def stop(self, kernel) -> None:
        """Clean up smart home plugin."""
        self.connected = False
        print("[SmartHomePlugin] Shut down")

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle smart home WebSocket messages."""
        msg_type = message.get("type")

        if msg_type == "smart_home_action":
            action = message.get("action")
            device = message.get("device")

            if action == "turn_on" and self.connected:
                return {
                    "type": "smart_home_result",
                    "action": "turn_on",
                    "device": device,
                    "success": True,
                    "message": f"{device} turned on"
                }

            elif action == "turn_off" and self.connected:
                return {
                    "type": "smart_home_result",
                    "action": "turn_off",
                    "device": device,
                    "success": True,
                    "message": f"{device} turned off"
                }

        return None

    async def handle_command(self, handler: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle command dispatcher output."""
        if handler == "smart_home_turn_on":
            device = params.get("device", "lights")
            return {
                "success": True,
                "narration": f"Turning on the {device}.",
                "extra_data": {"device": device, "action": "turn_on"}
            }
        elif handler == "smart_home_turn_off":
            device = params.get("device", "lights")
            return {
                "success": True,
                "narration": f"Turning off the {device}.",
                "extra_data": {"device": device, "action": "turn_off"}
            }
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Return plugin status."""
        return {
            "healthy": self.connected,
            "name": self.name
        }