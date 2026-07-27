# Routines & Automation

## Overview
Multi-step voice commands with progress feedback.

## Built-in Routines

### Good Night
- Lock PC
- Dim lights
- Set do-not-disturb

### I'm Leaving
- Shutdown services
- Lock PC
- Turn off lights

### Work Mode
- Open specific apps
- Set volume
- Enable focus lights

### Movie Time
- Dim lights
- Open media app
- Set volume

## Custom Routines
- User-defined via voice
- "Create a routine called X that does Y, Z"
- Stored as JSON

## Components

### Routine Service
- Define/execute routines
- Progress tracking
- File: `backend/app/services/routine_service.py`

## WebSocket Events
- `run_routine` — execute routine
- `create_routine` — define new routine
- `list_routines` — show available
- `delete_routine` — remove routine
- `routine_progress` — step progress

## Voice Commands
- "Run routine good night"
- "Create routine..."
- "List routines"
- "Delete routine..."

## Related

- [[JARVIS_ENHANCEMENT_PLAN]] — Phase 4 routines
- [[Smart Home Integration]] — device control
- [[API_DOCS]] — routine events
- [[Memory Map]] — vault index
