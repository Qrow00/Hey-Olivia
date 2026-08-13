"""AppKernel - J.A.R.V.I.S. V3 Application Kernel.

Responsible for:
- Plugin registration and lifecycle management
- JARVIS_SERVICES env var gating → plugin enable/disable
- Ordered startup/shutdown orchestration
- Change notification to StateStore on service start/stop
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path


class AppKernel:
    """Core application kernel that manages plugin lifecycle and orchestration."""
    
    def __init__(self, env_vars: Optional[Dict[str, str]] = None):
        self.env_vars = env_vars or {}
        self.plugins: Dict[str, Any] = {}
        self.enabled: Dict[str, bool] = {}
        self.state_store = None
        self.startup_complete = False
        
    def parse_services(self, env_value: str = "minimal") -> Dict[str, bool]:
        """Parse JARVIS_SERVICES env var → {plugin_name: enabled_bool}."""
        SERVICE_TO_PLUGIN = {
            "voice": ["voice_pipeline"],
            "smart_home": ["smart_home_plugin", "mqtt_service"],
            "browser": ["browser_automation"],
            "vision": ["vision_plugin"],
            "monitoring": ["monitoring_plugin"],
            "wearable": ["wearable_service"],
            "thermal": ["thermal_logger"],
            "mqtt": ["mqtt_service"],
        }
        
        ALL_PLUGINS = {
            "voice_pipeline", "smart_home_plugin", "browser_automation",
            "vision_plugin", "monitoring_plugin", "wearable_service",
            "thermal_logger", "mqtt_service",
        }
        
        enabled = {}
        parts = env_value.strip().lower().split()
        
        if not parts or parts[0] == "full":
            for p in ALL_PLUGINS:
                enabled[p] = True
            self.enabled = enabled
            return enabled
        
        for service in parts:
            for p in SERVICE_TO_PLUGIN.get(service, []):
                enabled[p] = True
        
        # Default: voice always enabled
        enabled["voice_pipeline"] = True
        
        self.enabled = enabled
        return enabled
    
    async def startup(self, state_store=None) -> None:
        """Ordered startup sequence."""
        self.state_store = state_store
        
        # Parse services from env var
        env_value = self.env_vars.get("JARVIS_SERVICES", "minimal")
        self.enabled = self.parse_services(env_value)
        
        # Plugin start order matters - voice first
        startup_order = [
            "voice_pipeline",       # Always start first
            "smart_home_plugin",    # If enabled
            "monitoring_plugin",    # If enabled
            "browser_automation",   # If enabled
            "vision_plugin",        # If enabled (optional)
            "wearable_service",     # If enabled
            "thermal_logger",       # If enabled
            "mqtt_service",         # If enabled
        ]
        
        # Start plugins in order
        for plugin_name in startup_order:
            if self.enabled.get(plugin_name, False):
                await self._start_plugin(plugin_name)
        
        self.startup_complete = True
        
        # Notify StateStore
        if self.state_store:
            await self.state_store.broadcast({
                "type": "kernel_started",
                "enabled_plugins": list(self.enabled.keys()),
                "active_profile": self.state_store.get_active_profile() if self.state_store else "default"
            })
    
    async def _start_plugin(self, plugin_name: str) -> None:
        """Start a single plugin."""
        if plugin_name in self.plugins:
            return
        
        # Dynamically import and instantiate plugin
        try:
            if plugin_name == "voice_pipeline":
                from .plugins.voice_pipeline import VoicePipelinePlugin
                plugin = VoicePipelinePlugin()
            elif plugin_name == "smart_home_plugin":
                from .plugins.smart_home import SmartHomePlugin
                plugin = SmartHomePlugin()
            elif plugin_name == "monitoring_plugin":
                from .plugins.monitoring import MonitoringPlugin
                plugin = MonitoringPlugin()
            elif plugin_name == "browser_automation":
                from .plugins.browser_automation import BrowserAutomationPlugin
                plugin = BrowserAutomationPlugin()
            elif plugin_name == "vision_plugin":
                from .plugins.vision import VisionPlugin
                plugin = VisionPlugin()
            elif plugin_name == "wearable_service":
                from .plugins.wearable import WearablePlugin
                plugin = WearablePlugin()
            elif plugin_name == "thermal_logger":
                from .plugins.thermal import ThermalLoggerPlugin
                plugin = ThermalLoggerPlugin()
            elif plugin_name == "mqtt_service":
                from .plugins.mqtt import MQTTPlugin
                plugin = MQTTPlugin()
            else:
                return
            
            await plugin.start(self)
            self.plugins[plugin_name] = plugin
            
        except ImportError as e:
            print(f"Plugin {plugin_name} not available: {e}")
        except Exception as e:
            print(f"Failed to start plugin {plugin_name}: {e}")
    
    async def shutdown(self) -> None:
        """Ordered shutdown sequence."""
        # Reverse order of startup (reverse startup_order)
        shutdown_order = list(self.plugins.keys())
        
        for plugin_name in reversed(shutdown_order):
            await self._stop_plugin(plugin_name)
        
        self.plugins.clear()
        self.startup_complete = False
        self.enabled = {}
        
        # Notify StateStore
        if self.state_store:
            await self.state_store.broadcast({
                "type": "kernel_shutdown",
                "message": "J.A.R.V.I.S. V3 shutting down"
            })
    
    async def _stop_plugin(self, plugin_name: str) -> None:
        """Stop a single plugin."""
        if plugin_name not in self.plugins:
            return
        
        plugin = self.plugins[plugin_name]
        try:
            await plugin.stop(self)
        except Exception as e:
            print(f"Error stopping plugin {plugin_name}: {e}")
        finally:
            del self.plugins[plugin_name]
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a registered plugin by name."""
        return self.plugins.get(name)
    
    def is_plugin_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled."""
        return self.enabled.get(name, False)
    
    @property
    def active_plugins(self) -> List[str]:
        """Return list of enabled plugin names."""
        return list(self.enabled.keys())