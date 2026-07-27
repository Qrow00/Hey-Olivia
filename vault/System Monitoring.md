# System Monitoring

## Overview
Proactive system awareness — Jarvis watches your PC and reports issues.

## Metrics Monitored
- CPU usage
- RAM usage
- Disk space
- GPU temperature (RX 6600)
- Network status

## Alert Thresholds
- Disk > 90% full
- GPU > 85°C
- RAM > 85% usage

## Components

### System Monitor
- Background polling every 30s
- SQLite ring buffer storage
- File: `backend/app/services/monitoring_service.py`

### Alert Engine
- Threshold-based triggers
- Voice + notification alerts
- File: `backend/app/services/alert_engine.py`

### Activity Logger
- Running processes
- Active windows
- File changes
- File: `backend/app/services/activity_logger.py`

## WebSocket Events
- `monitoring_snapshot` — current metrics
- `monitoring_history` — metrics over time
- `monitoring_alerts` — alert history
- `activity_log` — recent activity
- `activity_window` — active window history

## Voice Commands
- "System health"
- "Get alerts"
- "Activity log"
- "What's running?"

## Related

- [[JARVIS_ENHANCEMENT_PLAN]] — Phase 1 monitoring
- [[API_DOCS]] — monitoring events
- [[AGENTS]] — GPU specs (RX 6600)
- [[Memory Map]] — vault index
