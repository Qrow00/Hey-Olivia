from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class PluginInfo:
    id: str
    name: str
    version: str
    description: str
    author: str = ""
    capabilities: list[str] = field(default_factory=list)
    enabled: bool = True


class DevicePlugin(ABC):
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        pass

    @abstractmethod
    async def initialize(self, config: dict = None) -> bool:
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        pass

    @abstractmethod
    async def handle_command(self, command: str, params: dict) -> dict:
        pass

    async def on_device_connected(self, device_id: str, device_info: dict) -> Optional[dict]:
        return None

    async def on_device_disconnected(self, device_id: str) -> Optional[dict]:
        return None

    async def get_status(self) -> dict:
        return {"plugin": self.info.id, "status": "active"}

    def supports_capability(self, capability: str) -> bool:
        return capability in self.info.capabilities
