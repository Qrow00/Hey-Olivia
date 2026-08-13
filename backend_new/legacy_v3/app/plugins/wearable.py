"""WearablePlugin - Health metrics from paired wearables.

In production: MQTT/BLE integration for heart rate, steps, calories, battery.
"""

from app.plugins.base import BasePlugin
import asyncio
from typing import Dict, Any, Optional


class WearablePlugin(BasePlugin):
    """Wearable health metrics plugin."""

    name = "wearable_service"

    def __init__(self):
        super().__init__()
        self.available = False
        self.health_metrics: Dict[str, Any] = {}

    async def start(self, kernel) -> None:
        """Initialize wearable plugin."""
        self.available = True
        print("[WearablePlugin] Initialized")

    async def stop(self, kernel) -> None:
        """Clean up wearable plugin."""
        self.available = False
        print("[WearablePlugin] Shut down")

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle wearable WebSocket messages."""
        msg_type = message.get("type")
        if msg_type == "get_health":
            return {
                "type": "health_data",
                "data": self.health_metrics,
                "success": True
            }
        return None

    async def handle_command(self, handler: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle command dispatcher output."""
        if handler == "wearable_status":
            return {"success": True, "narration": "Checking health metrics."}
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Return plugin status."""
        return {"healthy": self.available, "name": self.name}