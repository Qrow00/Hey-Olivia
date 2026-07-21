---
name: jarvis-browser
description: Use when the user asks to browse the web, search Google, visit a website, open a URL, scrape content, fill forms, or perform any browser automation task through JARVIS.
---

# JARVIS Browser Skill

This skill enables JARVIS to control a web browser through voice commands or text input. It uses the Hermes Browser Service running on the FastAPI backend with Playwright.

## Capabilities

- Navigate to URLs
- Google search
- Click elements on pages
- Type into forms
- Take screenshots
- Extract page content
- Scroll up/down
- Go back/forward
- Get accessibility tree snapshots

## WebSocket Message Types

### Create Session
```json
{
  "type": "browser_create_session",
  "session_id": "default",
  "viewport_width": 1280,
  "viewport_height": 720
}
```

### Navigate
```json
{
  "type": "browser_navigate",
  "session_id": "default",
  "url": "https://example.com"
}
```

### Click Element
```json
{
  "type": "browser_click",
  "session_id": "default",
  "ref": "@e1"
}
```

### Type Text
```json
{
  "type": "browser_type",
  "session_id": "default",
  "ref": "@e2",
  "text": "Hello World"
}
```

### Google Search
```json
{
  "type": "browser_search",
  "session_id": "default",
  "query": "Flutter documentation"
}
```

### Screenshot
```json
{
  "type": "browser_screenshot",
  "session_id": "default"
}
```

### Accessibility Snapshot
```json
{
  "type": "browser_snapshot",
  "session_id": "default"
}
```

### Scroll
```json
{
  "type": "browser_scroll",
  "session_id": "default",
  "direction": "down",
  "amount": 500
}
```

## Voice Command Examples

- "Search Google for [query]"
- "Open [website]"
- "Go to [url]"
- "Click [element]"
- "Type [text] in [field]"
- "Take a screenshot"
- "Scroll down"
- "Go back"
- "What's on the page?"

## Response Types

- `browser_session_created` - Session started
- `browser_navigating` - Loading page
- `browser_navigate_result` - Navigation complete
- `browser_screenshot` - Screenshot captured (base64 JPEG)
- `browser_snapshot` - Accessibility tree
- `browser_search_result` - Search results
- `browser_click_result` - Click action result
- `browser_type_result` - Type action result
- `browser_scroll_result` - Scroll action result

## Safety Notes

- Sessions auto-cleanup after 30 minutes of inactivity
- Cookies are persisted for login reuse
- Confirm before submitting forms or making purchases
- Rate limit requests to avoid being blocked
