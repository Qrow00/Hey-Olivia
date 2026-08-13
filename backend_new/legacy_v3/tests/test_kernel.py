"""Kernel service parsing tests using Test-Driven Development."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_services_full_enables_all():
    """RED: Full service mode enables all plugins."""
    from app.kernel import AppKernel
    kernel = AppKernel()
    kernel.parse_services("full")
    expected = {
        "voice_pipeline", "smart_home_plugin", "browser_automation",
        "vision_plugin", "monitoring_plugin", "wearable_service",
        "thermal_logger", "mqtt_service"
    }
    assert kernel.enabled.keys() == expected
    print("✓ Full mode: All plugins enabled")

def test_services_minimal_only_voice():
    """RED: Minimal mode enables only voice."""
    from app.kernel import AppKernel
    kernel = AppKernel()
    kernel.parse_services("minimal")
    assert "voice_pipeline" in kernel.enabled
    assert "smart_home_plugin" not in kernel.enabled
    print("✓ Minimal mode: Only voice enabled")

def test_services_smart_home():
    """RED: Smart home services enable relevant plugins."""
    from app.kernel import AppKernel
    kernel = AppKernel()
    kernel.parse_services("smart_home")
    assert kernel.enabled.get("smart_home_plugin") == True
    assert kernel.enabled.get("mqtt_service") == True
    assert kernel.enabled.get("voice_pipeline") == True  # Default
    print("✓ Smart home: smart_home_plugin + mqtt_service enabled")

def test_services_browser():
    """RED: Browser services enable browser plugin."""
    from app.kernel import AppKernel
    kernel = AppKernel()
    kernel.parse_services("browser")
    assert kernel.enabled.get("browser_automation") == True
    assert kernel.enabled.get("voice_pipeline") == True  # Default
    print("✓ Browser: browser_automation enabled")

def test_services_voice_always():
    """RED: Voice is always enabled as default."""
    from app.kernel import AppKernel
    kernel = AppKernel()
    kernel.parse_services("voice")
    assert kernel.enabled.get("voice_pipeline") == True
    print("✓ Voice: voice_pipeline always default")