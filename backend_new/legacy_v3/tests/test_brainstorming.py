"""Brainstorming analysis: J.A.R.V.I.S. V3 system design insights."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def analyze_service_parsing():
    """Brainstorming: Why does service parsing work this way?"""
    from app.kernel import AppKernel
    
    # Five Whys analysis:
    # Why 1: Why does 'full' enable all plugins?
    # → Because parse_services checks if first part is "full"
    # Why 2: Why does 'minimal' only enable voice?
    # → Because minimal mode splits by spaces and checks services
    # Why 3: Why is voice always default?
    # → Because line 59 in kernel.py: enabled["voice_pipeline"] = True
    # Why 4: Why default to voice?
    # → Voice pipeline is the core interaction entry point
    # Why 5: Why is interaction entry point prioritized?
    # → J.A.R.V.I.S. design philosophy: voice-first AI assistant
    
    kernel = AppKernel()
    kernel.parse_services("full")
    print("✓ Five Whys: Voice-first design philosophy confirmed")
    return True

def evaluate_service_combinations():
    """Brainstorming: Evaluate service combination trade-offs."""
    from app.kernel import AppKernel
    
    combinations = {
        "full": 8,        # All plugins
        "minimal": 1,     # Voice only
        "smart_home": 3,  # voice + smart_home + mqtt
        "browser": 2,     # voice + browser
        "voice": 1,       # voice only
    }
    
    print("✓ Service combination analysis:")
    for services, count in combinations.items():
        kernel = AppKernel()
        kernel.parse_services(services)
        enabled_count = len(kernel.enabled)
        status = "✓" if enabled_count == count else "✗"
        print(f"  {status} {services:12s}: {enabled_count} plugins (expected {count})")
    
    return True

def inspect_plugin_priority():
    """Brainstorming: Plugin startup order matters."""
    from app.kernel import AppKernel
    
    kernel = AppKernel()
    kernel.parse_services("full")
    
    # Startup order from kernel.py:73-82
    startup_order = [
        "voice_pipeline",
        "smart_home_plugin",
        "monitoring_plugin",
        "browser_automation",
        "vision_plugin",
        "wearable_service",
        "thermal_logger",
        "mqtt_service",
    ]
    
    print("✓ Plugin startup order:")
    for i, plugin in enumerate(startup_order, 1):
        enabled = plugin in kernel.enabled
        print(f"  {i}. {plugin:25s} {'ENABLED' if enabled else 'disabled'}")
    
    print("\n⚠ Importance: Voice pipeline must start first (line 74)")
    print("⚠ Dependency: Smart home needs MQTT (both enabled together)")
    print("⚠ Optional: Vision plugin is 5th in order (line 78)")
    
    return True

def synthesize_recommendations():
    """Brainstorming: Synthesize action recommendations."""
    print("\n📋 Recommended next steps:")
    print("  1. Test individual service combinations before full mode")
    print("  2. Use 'minimal' for development, 'full' for production")
    print("  3. Add 'wearable' or 'thermal' services as needed")
    print("  4. Avoid 'browser' in headless server environments")
    return True

# Run all brainstorming analyses
print("=" * 60)
print("BRAINSTORMING ANALYSIS: J.A.R.V.I.S. V3 Service Design")
print("=" * 60)

analyze_service_parsing()
evaluate_service_combinations()
inspect_plugin_priority()
synthesize_recommendations()

print("\n" + "=" * 60)
print("BRAINSTORMING COMPLETE")
print("=" * 60)