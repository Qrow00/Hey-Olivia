"""BasePlugin - Base class for all J.A.R.V.I.S. V3 plugins.

Each plugin is responsible for a specific domain capability:
- Smart Home Control
- Browser Automation
- Vision/Camera Analysis
- Monitoring & Alerts
- Wearable Health Metrics
- Thermal Diagnostics
"""

import abc
import asyncio
from typing import Dict, Any, Optional, List



class BasePlugin(abc.ABC):
    """Base class for all J.A.R.V.I.S. V3 plugins."""
    
    name: str = "base_plugin"
    enabled: bool = False
    
    def __init__(self):
        self._registered_intents: List[str] = []
    
    @abc.abstractmethod
    async def start(self, kernel) -> None:
        """Called by AppKernel during startup.
        
        Register WebSocket message types, initialize resources (MQTT, Playwright, etc.).
        """
        pass
    
    @abc.abstractmethod
    async def stop(self, kernel) -> None:
        """Called by AppKernel during shutdown.
        
        Clean up resources, unregister message types.
        """
        pass
    
    @abc.abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming WebSocket message.
        
        Return {success, response} or None if message not handled.
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Return status for monitoring dashboards.
        
        Default implementation returns healthy=True.
        Subclasses should override for meaningful status.
        """
        return {"healthy": True, "name": self.name, "details": "Plugin operational"}
    
    async def handle_intent(self, intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a recognized intent/ command.
        
        Subclasses override this to handle specific commands.
        Return {success, text, data} if handled, else None.
        """
        return None
    
    async def handle_command(self, handler: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a specific command handler with parameters.
        
        Subclasses override this for command execution.
        Return {success, text, data} if handled, else None.
        """
        return None