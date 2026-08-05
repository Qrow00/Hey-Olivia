import os
import re
import shutil
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional

# Ollama restored native SM60/SM61 kernels in v0.12.0 (issue #12316 fixed, FA
# for CC 6.x in #16994). Older builds ship CUDA 13 PTX that Pascal cannot JIT.
MIN_OLLAMA_VERSION = (0, 12, 0)
MIN_GPU_COMPUTE_CAP = (6, 0)


@dataclass
class GpuInfo:
    vendor: str = "none"
    name: str = "CPU"
    compute_capability: str = ""
    vram_mb: int = 0
    driver: str = ""
    cuda_available: bool = False


def _run(cmd: list) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        return ""


def detect_gpu() -> GpuInfo:
    smi = shutil.which("nvidia-smi")
    if smi:
        raw = _run([smi, "--query-gpu=name,memory.total,driver_version,compute_cap", "--format=csv,noheader"])
        if raw:
            parts = [p.strip() for p in raw.split(",")]
            cc = parts[3] if len(parts) > 3 else ""
            return GpuInfo(
                vendor="nvidia",
                name=parts[0] if parts else "NVIDIA GPU",
                compute_capability=cc,
                vram_mb=_parse_vram(parts[1]) if len(parts) > 1 else 0,
                driver=parts[2] if len(parts) > 2 else "",
                cuda_available=True,
            )
    return GpuInfo()


def _parse_vram(text: str) -> int:
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else 0


def _parse_cc(cc: str) -> Optional[tuple]:
    m = re.match(r"(\d+)\.(\d+)", cc)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _parse_version(text: str) -> Optional[tuple]:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(x) for x in m.groups()) if m else None


PROJECT_OLLAMA = r"D:\project\Jarvis project\Hey-Olivia\backend\ollama\ollama.exe"


def ollama_version() -> Optional[tuple]:
    exe = shutil.which("ollama") or (PROJECT_OLLAMA if os.path.exists(PROJECT_OLLAMA) else None)
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10)
        return _parse_version(out.stdout) or _parse_version(out.stderr)
    except Exception:
        return None


def ollama_use_cpu(gpu: Optional[GpuInfo] = None) -> bool:
    gpu = gpu or detect_gpu()
    if gpu.vendor != "nvidia" or not gpu.compute_capability:
        return True
    cc = _parse_cc(gpu.compute_capability)
    if cc is None:
        return True
    override = os.environ.get("OLLAMA_MIN_COMPUTE_CAP")
    if override:
        try:
            min_parts = [int(x) for x in override.split(".")]
            return (cc[0], cc[1]) < (min_parts[0], min_parts[1])
        except ValueError:
            pass
    ver = ollama_version()
    if ver is not None and ver < MIN_OLLAMA_VERSION:
        return True
    return (cc[0], cc[1]) < MIN_GPU_COMPUTE_CAP


def ollama_llm_library(gpu: Optional[GpuInfo] = None) -> str:
    if ollama_use_cpu(gpu):
        return "cpu"
    return ""


def stt_device(gpu: Optional[GpuInfo] = None) -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def get_hardware_profile(gpu: Optional[GpuInfo] = None) -> dict:
    gpu = gpu or detect_gpu()
    return {
        "gpu": asdict(gpu),
        "ollama_version": ollama_version(),
        "ollama_use_cpu": ollama_use_cpu(gpu),
        "ollama_llm_library": ollama_llm_library(gpu) or "auto",
        "stt_device": stt_device(gpu),
    }
