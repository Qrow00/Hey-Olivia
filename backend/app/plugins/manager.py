import os
import json
import importlib
from typing import Optional
from app.plugins.base import DevicePlugin, PluginInfo


class PluginManager:
    def __init__(self):
        self.plugins: dict[str, DevicePlugin] = {}
        self._capability_map: dict[str, str] = {}
        self._config_path = "plugins_config.json"
        self._load_config()

    def _load_config(self):
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r") as f:
                    self._config = json.load(f)
            except:
                self._config = {"plugins": {}}
        else:
            self._config = {"plugins": {}}

    def _save_config(self):
        with open(self._config_path, "w") as f:
            json.dump(self._config, f, indent=2)

    async def register_plugin(self, plugin: DevicePlugin, config: dict = None) -> dict:
        info = plugin.info

        if info.id in self.plugins:
            return {"status": "error", "message": f"Plugin {info.id} already registered"}

        try:
            success = await plugin.initialize(config or self._config.get("plugins", {}).get(info.id, {}))
            if not success:
                return {"status": "error", "message": f"Plugin {info.id} initialization failed"}
        except Exception as e:
            return {"status": "error", "message": f"Plugin {info.id} init error: {str(e)}"}

        self.plugins[info.id] = plugin

        for cap in info.capabilities:
            if cap not in self._capability_map:
                self._capability_map[cap] = info.id

        self._config["plugins"][info.id] = {
            "enabled": info.enabled,
            "version": info.version,
        }
        self._save_config()

        return {
            "status": "registered",
            "plugin_id": info.id,
            "name": info.name,
            "version": info.version,
            "capabilities": info.capabilities,
        }

    async def unregister_plugin(self, plugin_id: str) -> dict:
        plugin = self.plugins.pop(plugin_id, None)
        if not plugin:
            return {"status": "error", "message": f"Plugin {plugin_id} not found"}

        try:
            await plugin.shutdown()
        except:
            pass

        for cap in plugin.info.capabilities:
            if self._capability_map.get(cap) == plugin_id:
                del self._capability_map[cap]

        self._config.get("plugins", {}).pop(plugin_id, None)
        self._save_config()

        return {"status": "unregistered", "plugin_id": plugin_id}

    def get_plugin(self, plugin_id: str) -> Optional[DevicePlugin]:
        return self.plugins.get(plugin_id)

    def get_plugin_for_capability(self, capability: str) -> Optional[DevicePlugin]:
        plugin_id = self._capability_map.get(capability)
        if plugin_id:
            return self.plugins.get(plugin_id)
        return None

    async def handle_command(self, capability: str, command: str, params: dict = None) -> dict:
        plugin = self.get_plugin_for_capability(capability)
        if not plugin:
            return {
                "status": "error",
                "message": f"No plugin registered for capability: {capability}",
            }

        if not plugin.info.enabled:
            return {
                "status": "error",
                "message": f"Plugin {plugin.info.id} is disabled",
            }

        try:
            return await plugin.handle_command(command, params or {})
        except Exception as e:
            return {
                "status": "error",
                "message": f"Plugin {plugin.info.id} command error: {str(e)}",
            }

    async def on_device_connected(self, device_id: str, device_info: dict) -> list[dict]:
        results = []
        for plugin in self.plugins.values():
            if plugin.info.enabled:
                try:
                    result = await plugin.on_device_connected(device_id, device_info)
                    if result:
                        results.append(result)
                except:
                    pass
        return results

    async def on_device_disconnected(self, device_id: str) -> list[dict]:
        results = []
        for plugin in self.plugins.values():
            if plugin.info.enabled:
                try:
                    result = await plugin.on_device_disconnected(device_id)
                    if result:
                        results.append(result)
                except:
                    pass
        return results

    async def get_all_status(self) -> list[dict]:
        statuses = []
        for plugin in self.plugins.values():
            try:
                status = await plugin.get_status()
                statuses.append(status)
            except:
                statuses.append({"plugin": plugin.info.id, "status": "error"})
        return statuses

    def get_all_plugins(self) -> list[dict]:
        return [
            {
                "id": p.info.id,
                "name": p.info.name,
                "version": p.info.version,
                "description": p.info.description,
                "author": p.info.author,
                "capabilities": p.info.capabilities,
                "enabled": p.info.enabled,
            }
            for p in self.plugins.values()
        ]

    def get_capabilities(self) -> dict[str, str]:
        return dict(self._capability_map)

    def has_capability(self, capability: str) -> bool:
        return capability in self._capability_map

    def set_enabled(self, plugin_id: str, enabled: bool) -> dict:
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return {"status": "error", "message": "Plugin not found"}

        plugin.info.enabled = enabled
        self._config["plugins"][plugin_id] = {
            "enabled": enabled,
            "version": plugin.info.version,
        }
        self._save_config()

        return {"status": "updated", "plugin_id": plugin_id, "enabled": enabled}


plugin_manager = PluginManager()
