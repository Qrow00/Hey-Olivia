"""ThermalLoggerPlugin - Thermal diagnostics logging for ASUS GL553VD.

For ASUS GL553VD laptop random shutdown diagnosis.
Records: timestamp, cpu_temp, gpu_temp, fan_speed, load%.
Uses WMI on Windows for hardware sensor data.
"""

import asyncio
import datetime
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import psutil
import wmi


class ThermalLoggerPlugin(BasePlugin):
    """Thermal diagnostics logging plugin for ASUS GL553VD shutdown diagnosis."""

    name = "thermal_logger"

    def __init__(self):
        super().__init__()
        self.log_dir = Path("data/logs")
        self.interval = 30  # seconds
        self._task: Optional[asyncio.Task] = None
        self.logging_enabled = False
        self._wmi_conn: Optional[wmi.WMI] = None
        self._gpu_temp_available = False

    async def start(self, kernel) -> None:
        """Start thermal logging loop."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._init_wmi()
        self.logging_enabled = True
        self._task = asyncio.create_task(self._log_loop())
        print("[ThermalLoggerPlugin] Started thermal logging")

    async def stop(self, kernel) -> None:
        """Stop thermal logging."""
        self.logging_enabled = False
        if self._task:
            self._task.cancel()
            self._task = None
        print("[ThermalLoggerPlugin] Stopped thermal logging")

    def _init_wmi(self) -> None:
        """Initialize WMI connection for hardware sensors."""
        try:
            self._wmi_conn = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            # Check if OpenHardwareMonitor is available
            sensors = self._wmi_conn.Sensor()
            for sensor in sensors:
                if sensor.SensorType == "Temperature" and "GPU" in sensor.Name:
                    self._gpu_temp_available = True
                    break
            print(f"[ThermalLoggerPlugin] WMI initialized, GPU temp: {self._gpu_temp_available}")
        except Exception as e:
            print(f"[ThermalLoggerPlugin] WMI not available (OpenHardwareMonitor not running): {e}")
            self._wmi_conn = None

    async def _log_loop(self) -> None:
        """Main thermal logging loop."""
        while self.logging_enabled:
            try:
                await asyncio.sleep(self.interval)
                if not self.logging_enabled:
                    break

                entry = await self._collect_thermal_data()
                self._write_entry(entry)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ThermalLoggerPlugin] Logging error: {e}")

    async def _collect_thermal_data(self) -> Dict[str, Any]:
        """Collect thermal metrics from WMI and psutil."""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "cpu_temp": None,
            "gpu_temp": None,
            "fan_speed": None,
            "cpu_load": None,
            "ram_percent": None,
        }

        # CPU load and RAM from psutil
        try:
            entry["cpu_load"] = psutil.cpu_percent(interval=0.1)
            entry["ram_percent"] = psutil.virtual_memory().percent
        except Exception:
            pass

        # Temperature and fan from WMI (OpenHardwareMonitor)
        if self._wmi_conn:
            try:
                sensors = self._wmi_conn.Sensor()
                for sensor in sensors:
                    if sensor.SensorType == "Temperature":
                        if "CPU" in sensor.Name or "Core" in sensor.Name:
                            if entry["cpu_temp"] is None or sensor.Value > entry["cpu_temp"]:
                                entry["cpu_temp"] = sensor.Value
                        elif "GPU" in sensor.Name:
                            entry["gpu_temp"] = sensor.Value
                    elif sensor.SensorType == "Fan":
                        if entry["fan_speed"] is None:
                            entry["fan_speed"] = sensor.Value
            except Exception as e:
                print(f"[ThermalLoggerPlugin] WMI sensor read error: {e}")

        return entry

    def _write_entry(self, entry: Dict[str, Any]) -> None:
        """Write thermal entry to TSV file."""
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"thermal_diag_{date_str}.tsv"
        header = "timestamp\tcpu_temp\tgpu_temp\tfan_speed\tcpu_load\tram_percent"
        line = "\t".join(str(entry.get(k, "")) for k in
                         ["timestamp", "cpu_temp", "gpu_temp", "fan_speed", "cpu_load", "ram_percent"])
        if not log_file.exists():
            log_file.write_text(header + "\n")
        with log_file.open("a") as f:
            f.write(line + "\n")

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle thermal WebSocket messages."""
        msg_type = message.get("type")

        if msg_type == "thermal_get_status":
            return await self.health_check()

        elif msg_type == "thermal_set_interval":
            new_interval = message.get("interval")
            if new_interval and isinstance(new_interval, int) and new_interval >= 5:
                self.interval = new_interval
                return {"success": True, "interval": self.interval}

        elif msg_type == "thermal_get_logs":
            date = message.get("date")  # YYYYMMDD
            if date:
                log_file = self.log_dir / f"thermal_diag_{date}.tsv"
                if log_file.exists():
                    content = log_file.read_text()
                    return {"success": True, "data": content}
            return {"success": False, "error": "Log file not found"}

        return None

    async def handle_command(self, handler: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle command dispatcher output."""
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Return plugin status."""
        return {
            "healthy": self.logging_enabled,
            "name": self.name,
            "interval": self.interval,
            "wmi_available": self._wmi_conn is not None,
            "gpu_temp_available": self._gpu_temp_available,
            "log_dir": str(self.log_dir),
        }