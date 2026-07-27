# Browser Automation

## Overview
Hermes browser for web automation, search, and content extraction.

## Engine
- **Playwright** — cross-browser automation
- **File:** `backend/app/services/hermes_browser.py`

## Capabilities
- Navigate to URLs
- Click elements
- Type text
- Take screenshots
- Extract page content
- Scroll pages
- Google search

## Endpoints
- `/api/v1/browser/sessions` — create session
- `/api/v1/browser/navigate` — go to URL
- `/api/v1/browser/click` — click element
- `/api/v1/browser/type` — enter text
- `/api/v1/browser/screenshot/{id}` — capture screen
- `/api/v1/browser/search` — Google search

## WebSocket Events
- `browser_create_session` — start browser
- `browser_navigate` — go to URL
- `browser_click` — click element
- `browser_screenshot` — get screenshot
- `browser_search` — search Google

## Voice Commands
- "Search for..."
- "Open website..."
- "What's on the screen?"

## Related

- [[AGENTS]] — Playwright configuration
- [[API_DOCS]] — browser endpoints
- [[Voice Pipeline]] — voice-driven browsing
- [[Memory Map]] — vault index
