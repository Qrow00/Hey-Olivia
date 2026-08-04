import os
import platform
import psutil

try:
    import GPUtil
    _HAS_GPUTIL = True
except ImportError:
    _HAS_GPUTIL = False


TIER_PRESETS = {
    "low": {
        "label": "Low-End",
        "description": "No GPU, 4-8GB RAM. Minimal features for smooth operation.",
        "models": {
            "llm": "qwen2.5:0.5b",
            "vision": None,
            "stt": "tiny",
            "embedding": None,
        },
        "features": {
            "browser": False,
            "vision": False,
            "wake_word": False,
            "screen_context": False,
            "activity_logger": False,
            "motion_detection": False,
        },
        "intervals": {
            "monitoring_poll_seconds": 120,
            "activity_poll_seconds": 300,
            "screen_context_poll_seconds": 600,
        },
        "limits": {
            "max_history": 20,
            "monitoring_max_history": 720,
            "activity_max_entries": 500,
            "screen_share_fps": 2,
            "screen_share_quality": 50,
            "max_browser_tabs": 1,
        },
    },
    "medium": {
        "label": "Mid-Range",
        "description": "Integrated or low-end GPU, 8-16GB RAM. Balanced features.",
        "models": {
            "llm": "llama3.2",
            "vision": "moondream",
            "stt": "tiny",
            "embedding": "nomic-embed-text",
        },
        "features": {
            "browser": True,
            "vision": True,
            "wake_word": False,
            "screen_context": False,
            "activity_logger": True,
            "motion_detection": True,
        },
        "intervals": {
            "monitoring_poll_seconds": 30,
            "activity_poll_seconds": 60,
            "screen_context_poll_seconds": 300,
        },
        "limits": {
            "max_history": 50,
            "monitoring_max_history": 2880,
            "activity_max_entries": 2000,
            "screen_share_fps": 5,
            "screen_share_quality": 80,
            "max_browser_tabs": 2,
        },
    },
    "high": {
        "label": "High-End",
        "description": "Dedicated GPU 8GB+ VRAM, 16GB+ RAM. Full feature set.",
        "models": {
            "llm": "llama3.2",
            "vision": "llava:7b",
            "stt": "tiny",
            "embedding": "nomic-embed-text",
        },
        "features": {
            "browser": True,
            "vision": True,
            "wake_word": True,
            "screen_context": True,
            "activity_logger": True,
            "motion_detection": True,
        },
        "intervals": {
            "monitoring_poll_seconds": 30,
            "activity_poll_seconds": 60,
            "screen_context_poll_seconds": 120,
        },
        "limits": {
            "max_history": 50,
            "monitoring_max_history": 2880,
            "activity_max_entries": 5000,
            "screen_share_fps": 5,
            "screen_share_quality": 80,
            "max_browser_tabs": 3,
        },
    },
}


class SystemConfigService:
    def __init__(self):
        self._active_config: dict = {}
        self._detected_specs: dict = {}

    def _detect_gpu(self) -> dict:
        gpu_info = {"name": None, "vram_gb": 0, "has_gpu": False}
        if _HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    g = gpus[0]
                    return {
                        "name": g.name,
                        "vram_gb": round(g.memoryTotal / 1024, 1),
                        "has_gpu": True,
                    }
            except Exception:
                pass
        if platform.system() == "Windows":
            try:
                import json
                import subprocess
                out = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                     "Get-CimInstance Win32_VideoController | "
                     "Select-Object Name, AdapterRAM | ConvertTo-Json -Compress"],
                    capture_output=True, text=True, timeout=10,
                ).stdout.strip()
                if out:
                    data = json.loads(out)
                    entries = data if isinstance(data, list) else [data]
                    if entries:
                        e = entries[0]
                        name = e.get("Name") or "Unknown GPU"
                        ram_bytes = e.get("AdapterRAM") or 0
                        vram_gb = round(ram_bytes / (1024**3), 1) if ram_bytes else 0
                        gpu_info = {"name": name, "vram_gb": vram_gb, "has_gpu": bool(vram_gb)}
            except Exception:
                pass
        return gpu_info

    def detect_specs(self) -> dict:
        ram = psutil.virtual_memory()
        ram_gb = round(ram.total / (1024**3), 1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_freq_ghz = round(cpu_freq.current / 1000, 2) if cpu_freq else 0

        gpu_info = self._detect_gpu()

        specs = {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor() or "Unknown",
            "cpu_count": cpu_count,
            "cpu_freq_ghz": cpu_freq_ghz,
            "ram_gb": ram_gb,
            "ram_available_gb": round(ram.available / (1024**3), 1),
            "gpu": gpu_info,
        }

        self._detected_specs = specs
        return specs

    def recommend_tier(self, specs: dict = None) -> str:
        if specs is None:
            specs = self._detected_specs or self.detect_specs()

        ram_gb = specs.get("ram_gb", 0)
        gpu = specs.get("gpu", {})
        has_gpu = gpu.get("has_gpu", False)
        vram_gb = gpu.get("vram_gb", 0)

        if has_gpu and vram_gb >= 3:
            if ram_gb >= 16 and vram_gb >= 6:
                return "high"
            return "medium"
        if ram_gb >= 12:
            return "medium"
        return "low"

    def _pick_installed_llm(self, candidates: list) -> str:
        try:
            import ollama
            installed = [m.model.split(":")[0] for m in ollama.list().models]
            for c in candidates:
                if c and c.split(":")[0] in installed:
                    return c
        except Exception:
            pass
        return candidates[0] if candidates else None

    def get_preset(self, tier: str) -> dict:
        return TIER_PRESETS.get(tier, TIER_PRESETS["medium"])

    def apply_tier(self, tier: str) -> dict:
        preset = self.get_preset(tier)
        self._active_config = {
            "tier": tier,
            **preset,
        }
        llm_model = preset.get("models", {}).get("llm")
        if llm_model:
            llm_model = self._pick_installed_llm([llm_model, "llama3.2", "phi4-mini"])
            try:
                from app.services.settings_service import settings_service
                settings_service.update("default", {"voice": {"llm_model": llm_model}})
            except Exception:
                pass
            try:
                from app.services.voice_service import voice_service
                voice_service.llm_model = llm_model
            except Exception:
                pass
            print(f"[SystemConfig] Applied tier '{tier}' -> LLM model: {llm_model}")
        return self._active_config

    def auto_adapt(self) -> dict:
        specs = self.detect_specs()
        tier = self.recommend_tier(specs)
        self.apply_tier(tier)
        print(
            f"[SystemConfig] Detected {specs['ram_gb']}GB RAM, "
            f"{specs['cpu_count']} cores, GPU={specs['gpu'].get('name')} "
            f"({specs['gpu'].get('vram_gb', 0)}GB) -> tier '{tier}'"
        )
        return self._active_config

    def get_active_config(self) -> dict:
        if not self._active_config:
            specs = self.detect_specs()
            tier = self.recommend_tier(specs)
            self.apply_tier(tier)
        return self._active_config

    def update_config(self, updates: dict) -> dict:
        config = self.get_active_config()

        for key in ("models", "features", "intervals", "limits"):
            if key in updates and isinstance(updates[key], dict):
                config[key] = {**config.get(key, {}), **updates[key]}

        if "tier" in updates:
            config["tier"] = updates["tier"]

        self._active_config = config
        return config

    def get_available_models(self) -> dict:
        try:
            import ollama
            response = ollama.list()
            installed = [m.model for m in response.models]
        except Exception:
            installed = []

        return {
            "installed": installed,
            "recommended": {
                "low": TIER_PRESETS["low"]["models"],
                "medium": TIER_PRESETS["medium"]["models"],
                "high": TIER_PRESETS["high"]["models"],
            },
        }


system_config_service = SystemConfigService()
