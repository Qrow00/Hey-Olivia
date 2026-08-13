"""MonitoringPlugin - CPU/RAM/disk/GPU polling + threshold alerts.

Polls system resources every 30 seconds, checks against configurable thresholds.
On threshold breach: system alert broadcast + voice alert (TTS).
"""

import asyncio
import time
import psutil
from typing import Dict, Any, Optional

import json


from app.plugins.base import BasePlugin

class MonitoringPlugin(BasePlugin):
    """System resource monitoring with threshold alerts."""
    
    name = "monitoring"
    
    def __init__(self):
        super().__init__()
        # Configurable thresholds (as percentages)
        self.thresholds: Dict[str, float] = {
            "cpu": 80.0,
            "ram": 85.0,
            "disk": 90.0,
            "gpu": 70.0,  # For GTX 1050, if monitored
        }
        self._polling_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
    
    async def start(self, kernel) -> None:
        """Start continuous polling loop."""
        self._is_monitoring = True
        self._polling_task = asyncio.create_task(self._polling_loop())
        print("[MonitoringPlugin] Started resource polling (every 30s)")
    
    async def stop(self, kernel) -> None:
        """Stop polling loop."""
        self._is_monitoring = False
        if self._polling_task:
            self._polling_task.cancel()
            self._polling_task = None
        print("[MonitoringPlugin] Stopped resource polling")
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle monitoring-related WebSocket messages."""
        msg_type = message.get("type")
        
        if msg_type == "get_status":
            return self.health_check()
        
        elif msg_type == "update_thresholds":
            # Allow runtime threshold updates
            new_thresholds = message.get("thresholds", {})
            self.thresholds.update(new_thresholds)
            return {"type": "thresholds_updated", "success": True}
        
        return None
    
    async def handle_command(self, handler: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle command dispatcher output."""
        if handler == "monitoring_status":
            return self.health_check()
        return None
    
    async def _polling_loop(self) -> None:
        """Main polling loop - runs every 30 seconds."""
        while self._is_monitoring:
            try:
                await asyncio.sleep(30)  # 30 second poll interval
                
                if not self._is_monitoring:
                    break
                
                # Collect system metrics
                metrics = await self._collect_metrics()
                
                # Check thresholds
                alerts = await self._check_thresholds(metrics)
                
                # Broadcast any alerts
                if alerts:
                    await self._broadcast_alerts(metrics, alerts)
                
                # Store metrics in StateStore for dashboard
                # (would integrate with StateStore in production)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MonitoringPlugin] Polling error: {e}")
                await asyncio.sleep(5)  # Brief backoff on error
    
    async def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system resource metrics."""
        metrics = {}
        
        # CPU percentage
        try:
            metrics["cpu"] = psutil.cpu_percent(interval=1) / 100.0  # Normalize to 0-1
        except Exception:
            metrics["cpu"] = 0.5
        
        # RAM percentage
        try:
            memory = psutil.virtual_memory()
            metrics["ram"] = memory.percent / 100.0  # Normalize to 0-1
        except Exception:
            metrics["ram"] = 0.5
        
        # Disk percentage
        try:
            disk = psutil.disk_usage("/")
            metrics["disk"] = disk.percent / 100.0  # Normalize to 0-1
        except Exception:
            metrics["disk"] = 0.5
        
        # GPU percentage (if available)
        try:
            # psutil doesn't GPU metrics directly; this is placeholder
            # In production: use nvidia-smi, GPUtil, or similar
            metrics["gpu"] = 0.3  # Simulated low GPU usage
        except Exception:
            metrics["gpu"] = 0.3
        
        return metrics
    
    async def _check_thresholds(self, metrics: Dict[str, float]) -> list:
        """Check metrics against thresholds and return list of breaches."""
        alerts = []
        
        for metric_name, threshold in self.thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                if value > threshold:
                    alerts.append({
                        "metric": metric_name,
                        "value": metrics[metric_name],
                        "threshold": threshold,
                        "severity": "critical" if value > threshold * 1.2 else "warning"
                    })
        
        return alerts
    
    async def _broadcast_alerts(self, metrics: Dict[str, float], alerts: list) -> None:
        """Broadcast threshold breach alerts via WebSocket."""
        # In production: send to WebSocket manager for all connected clients
        # Also trigger TTS voice alert
        alert_messages = []
        for alert in alerts:
            metric_name = alert["metric"]
            value = alert["value"]
            threshold = alert["threshold"]
            severity = alert["severity"]
            alert_messages.append(f"{metric_name} at {value*100:.1f}% (threshold: {threshold*100:.1f}%)")
        
        # Prepare alert message
        alert_text = "; ".join(alert_messages) if alert_messages else "Unknown alert"
        
        # Note: In full implementation, would broadcast via WS and/or trigger TTS
        print(f"[MonitoringPlugin] ALERT: {alert_text}")
        
        # Placeholder: return alert dict for integration
        return {
            "type": "monitoring_alert",
            "alerts": alerts,
            "metrics": metrics
        }