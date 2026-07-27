# Camera & Vision System

## Camera Types
- CCTV (RTSP streams)
- Doorbell cameras
- Indoor/outdoor cameras

## RTSP Integration
- Add cameras via API
- Stream to Flutter client
- Snapshot capture for analysis

## AI Vision

### Endpoints
- `/api/v1/vision/analyze` — analyze camera feed
- `/api/v1/vision/quick-look/{camera_id}` — quick look
- `/api/v1/vision/scan-all` — scan all cameras

### Models
- **llava:7b** — visual understanding
- **Whisper** — audio transcription from camera feeds

## Observation Mode
- Start continuous monitoring
- Alert on motion/activity
- Store analysis history

## Voice Commands
- "Show me the cameras"
- "What do you see?"
- "Watch the front door"
- "Scan cameras"

## Related

- [[DATA_STRUCTURE]] — CameraDevice schema
- [[API_DOCS]] — camera and vision endpoints
- [[Voice Pipeline]] — voice interaction
- [[Memory Map]] — vault index
