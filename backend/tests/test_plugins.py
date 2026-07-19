import pytest
from app.plugins.base import DevicePlugin, PluginInfo


class MockPlugin(DevicePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id="mock",
            name="Mock Plugin",
            version="0.1.0",
            description="Test plugin",
            author="Test",
            capabilities=["test_cap"],
        )

    async def initialize(self, config=None):
        return True

    async def shutdown(self):
        return True

    async def handle_command(self, command, params):
        return {"status": "ok", "echo": params}


def test_plugin_info():
    p = MockPlugin()
    assert p.info.id == "mock"
    assert "test_cap" in p.info.capabilities


def test_plugin_enabled_default():
    p = MockPlugin()
    assert p.info.enabled is True
