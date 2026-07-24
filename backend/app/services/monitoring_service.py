import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
import psutil

try:
    import GPUtil
    _HAS_GPUTIL = True
except ImportError:
    _HAS_GPUTIL = False


class MonitoringService:
    def __init__(self):
        self._polling = False
        self._poll_interval = 30
        self._latest: dict = {}
        self._history: list[dict] = []
        self._max_history = 2880  # 24h at 30s intervals
        self._listeners: list = []
        self._alert_thresholds = {
            "cpu_percent": 90.0,
            "ram_percent": 85.0,
            "disk_percent": 90.0,
            "gpu_temp": 85.0,
            "gpu_load": 95.0,
        }
        self._previous_alerts: dict[str, float] = {}
        self._alert_cooldown = 300

    def get_snapshot(self) -> dict:
        return self._latest.copy() if self._latest else self._collect_once()

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

    def _collect_once(self) -> dict:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        gpu_info = {}
        if _HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    g = gpus[0]
                    gpu_info = {
                        "gpu_name": g.name,
                        "gpu_load": round(g.load * 100, 1),
                        "gpu_memory_used": round(g.memoryUsed, 1),
                        "gpu_memory_total": round(g.memoryTotal, 1),
                        "gpu_memory_percent": round(g.memoryUsed / g.memoryTotal * 100, 1) if g.memoryTotal > 0 else 0,
                        "gpu_temp": round(g.temperature, 1) if g.temperature else 0,
                    }
            except Exception:
                pass

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
            ("cpu_percent", snapshot.get("cpu_percent", 0), "CPU Usage"),
            ("ram_percent", snapshot.get("ram_percent", 0), "RAM Usage"),
            ("disk_percent", snapshot.get("disk_percent", 0), "Disk Usage"),
            ("gpu_temp", snapshot.get("gpu_temp", 0), "GPU Temperature"),
            ("gpu_load", snapshot.get("gpu_load", 0), "GPU Load"),
        ]

        for metric, value, label in checks:
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
                        "message": f"{label} at {value}% (threshold: {threshold}%)",
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
