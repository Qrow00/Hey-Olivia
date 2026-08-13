"""Test backend imports work correctly."""
import sys
import os
import asyncio

# Add the backend_new directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_app_kernel_import():
    """Test that AppKernel can be imported."""
    from app.kernel import AppKernel
    kernel = AppKernel()
    assert kernel is not None
    assert kernel.enabled == {}

def test_state_store_import():
    """Test that StateStore can be imported."""
    from app.state_store import StateStore
    store = StateStore(db_path="test.db", data_dir="data")
    assert store is not None

def test_base_plugin_import():
    """Test that BasePlugin can be imported and instantiated."""
    from app.plugins.base import BasePlugin
    from asyncio import ensure_future
    
    # Create plugin class with concrete implementations
    class TestPlugin(BasePlugin):
        name = "test"
        
        async def start(self, kernel):
            pass
        
        async def stop(self, kernel):
            pass
        
        async def handle_message(self, message):
            return {"success": True, "response": "handled"}
    
    async def run_test():
        plugin = TestPlugin()
        health = await plugin.health_check()
        assert health["healthy"] == True
    
    asyncio.run(run_test())