import asyncio
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional
import psutil


class MonitoringService:
    def __init__(self):
        self._polling = False
        self._poll_interval = 3
        self._latest: dict = {}
        self._history: list[dict] = []
        self._max_history = 2880  # ~2.4h at 3s intervals
        self._cpu_warmed = False
        self._listeners: list = []
        self._alert_thresholds = {
            "cpu_percent": 90.0,
            "ram_percent": 85.0,
            "disk_percent": 90.0,
            "gpu_temp": 85.0,
            "gpu_load": 95.0,
            "process_count": 350.0,
            "top_process_memory_mb": 2048.0,
        }
        self._previous_alerts: dict[str, float] = {}
        self._alert_cooldown = 300
        self._process_cache: dict = {}
        self._process_cache_time = 0.0
        self._process_cache_ttl = 15

    def get_snapshot(self) -> dict:
        if self._latest and time.time() - self._latest.get("timestamp", 0) < self._poll_interval:
            return self._latest.copy()
        return self._collect_once()

    def get_history(self, minutes: int = 60) -> list[dict]:
        cutoff = time.time() - (minutes * 60)
        return [h for h in self._history if h.get("timestamp", 0) > cutoff]

    def get_alerts(self, limit: int = 20) -> list[dict]:
        alerts = [h for h in self._history if h.get("alert")]
        return alerts[-limit:]

    def set_threshold(self, metric: str, value: float):
        if metric in self._alert_thresholds:
            self._alert_thresholds[metric] = value

    def get_thresholds(self) -> dict:
        return self._alert_thresholds.copy()

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    def _cpu_sample(self) -> float:
        if not self._cpu_warmed:
            self._cpu_warmed = True
            return psutil.cpu_percent(interval=0.3) or 0.0
        return psutil.cpu_percent(interval=None) or 0.0

    def _gpu_info(self) -> dict:
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW,
            ).stdout.strip()
        except Exception:
            return {}
        parts = [p.strip() for p in out.split(",")]
        if len(parts) < 5:
            return {}
        try:
            load = float(parts[1])
            mem_used = float(parts[2])
            mem_total = float(parts[3])
            temp = float(parts[4])
        except ValueError:
            return {}
        return {
            "gpu_name": parts[0],
            "gpu_load": round(load, 1),
            "gpu_memory_used": round(mem_used, 1),
            "gpu_memory_total": round(mem_total, 1),
            "gpu_memory_percent": round(mem_used / mem_total * 100, 1) if mem_total > 0 else 0,
            "gpu_temp": temp,
        }

    def _process_info(self) -> dict:
        now = time.time()
        if self._process_cache and now - self._process_cache_time < self._process_cache_ttl:
            return self._process_cache
        try:
            procs = []
            for p in psutil.process_iter(["name", "memory_info"]):
                try:
                    name = p.info.get("name") or ""
                    mem = p.info.get("memory_info")
                    rss = mem.rss if mem else 0
                    procs.append((name, rss))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            return self._process_cache or {
                "process_count": 0,
                "top_process_name": "",
                "top_process_memory_mb": 0,
            }
        if procs:
            name, rss = max(procs, key=lambda x: x[1])
            result = {
                "process_count": len(procs),
                "top_process_name": name,
                "top_process_memory_mb": int(rss / (1024 ** 2)),
            }
        else:
            result = {"process_count": 0, "top_process_name": "", "top_process_memory_mb": 0}
        self._process_cache = result
        self._process_cache_time = now
        return result

    def _collect_once(self) -> dict:
        cpu = self._cpu_sample()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        gpu_info = self._gpu_info()

        net = psutil.net_io_counters()
        boot = psutil.boot_time()
        uptime = time.time() - boot

        snapshot = {
            "timestamp": time.time(),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": round(cpu, 1),
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": round(psutil.cpu_freq().current, 0) if psutil.cpu_freq() else 0,
            "ram_percent": round(ram.percent, 1),
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "net_sent_gb": round(net.bytes_sent / (1024**3), 3),
            "net_recv_gb": round(net.bytes_recv / (1024**3), 3),
            "uptime_hours": round(uptime / 3600, 1),
            "alert": False,
            "alert_details": [],
            **gpu_info,
            **self._process_info(),
        }

        alerts = self._check_thresholds(snapshot)
        if alerts:
            snapshot["alert"] = True
            snapshot["alert_details"] = alerts

        self._latest = snapshot
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return snapshot

    def _check_thresholds(self, snapshot: dict) -> list[dict]:
        alerts = []
        now = time.time()

        checks = [
            ("cpu_percent", snapshot.get("cpu_percent", 0), "CPU Usage", "%"),
            ("ram_percent", snapshot.get("ram_percent", 0), "RAM Usage", "%"),
            ("disk_percent", snapshot.get("disk_percent", 0), "Disk Usage", "%"),
            ("gpu_temp", snapshot.get("gpu_temp", 0), "GPU Temperature", "%"),
            ("gpu_load", snapshot.get("gpu_load", 0), "GPU Load", "%"),
            ("process_count", snapshot.get("process_count", 0), "Running Processes", ""),
            ("top_process_memory_mb", snapshot.get("top_process_memory_mb", 0), "Largest Process", " MB"),
        ]

        for metric, value, label, unit in checks:
            threshold = self._alert_thresholds.get(metric, 100)
            if value >= threshold:
                last_alert = self._previous_alerts.get(metric, 0)
                if now - last_alert >= self._alert_cooldown:
                    severity = "critical" if value >= threshold * 1.1 else "warning"
                    alerts.append({
                        "metric": metric,
                        "label": label,
                        "value": value,
                        "threshold": threshold,
                        "severity": severity,
                        "message": f"{label} at {value:g}{unit} (threshold: {threshold:g}{unit})",
                    })
                    self._previous_alerts[metric] = now

        return alerts

    async def _poll_loop(self):
        while self._polling:
            try:
                snapshot = await asyncio.to_thread(self._collect_once)

                if snapshot.get("alert"):
                    for alert in snapshot["alert_details"]:
                        for listener in self._listeners:
                            try:
                                await listener(alert)
                            except Exception:
                                pass

            except Exception as e:
                print(f"[MONITORING] Poll error: {e}")

            await asyncio.sleep(self._poll_interval)

    async def start_polling(self):
        if self._polling:
            return
        self._polling = True
        await asyncio.to_thread(self._collect_once)
        asyncio.create_task(self._poll_loop())
        print("[MONITORING] Started polling")

    async def stop_polling(self):
        self._polling = False
        print("[MONITORING] Stopped polling")


monitoring_service = MonitoringService()
