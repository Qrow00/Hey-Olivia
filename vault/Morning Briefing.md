# Morning Briefing

## Overview
One voice readout with everything important when you connect.

## Sources
- Weather (Open-Meteo API — free)
- System health (from monitoring)
- News (RSS feeds)
- Calendar (Google Calendar API)
- Smart home status

## Flow
```
Connect → Briefing Orchestrator → Assemble → edge-tts → Stream to client
```

## Components

### Briefing Orchestrator
- Calls all sources
- Assembles text
- File: `backend/app/services/briefing_service.py`

### Weather Service
- Open-Meteo API (no key required)
- Current conditions + forecast
- File: `backend/app/services/weather_service.py`

### News Service
- RSS feeds (configurable)
- Top 5 headlines
- File: `backend/app/services/news_service.py`

### Calendar Service
- Google Calendar API (OAuth)
- Today's events
- File: `backend/app/services/calendar_service.py`

## WebSocket Events
- `morning_briefing` — trigger briefing
- `briefing_config` — toggle sources
- `briefing_result` — generated briefing

## Voice Commands
- "Morning briefing"
- "Briefing config"

## Related

- [[JARVIS_ENHANCEMENT_PLAN]] — Phase 2 briefing
- [[Voice Pipeline]] — TTS output
- [[System Monitoring]] — system health source
- [[Memory Map]] — vault index
