# Personality System

## Overview
Jarvis personality — dry, British, occasionally witty (like Iron Man's JARVIS).

## Features

### Personality Enhancer
- Post-processes LLM responses
- Adds Jarvis flair
- File: `backend/app/services/personality_enhancer.py`

### British Wit Library
- Curated quips
- Dry observations
- Understated humor

### Contextual Remarks
- "Interesting code, sir"
- "Bold choice of variable names"
- Unsolicited observations

### Status Readouts
- "All systems nominal"
- "Running like a Swiss watch"

## Configuration
- Formal ↔ playful slider
- Quip frequency control
- Learn user preferences
- Remember opinions

## API Endpoints
- `/api/v1/personality` — get status
- `/api/v1/personality/style` — update traits
- `/api/v1/personality/opinion` — learn opinion
- `/api/v1/personality/feedback` — adjust from feedback

## Voice Commands
- "Personality config"
- "Set formality to 0.8"
- "Set quip frequency to high"

## Related

- [[JARVIS_ENHANCEMENT_PLAN]] — Phase 7 personality
- [[Voice Pipeline]] — TTS output
- [[API_DOCS]] — personality endpoints
- [[Memory Map]] — vault index
