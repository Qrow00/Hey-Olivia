# Device Mesh

## Overview
Multi-device orchestration for seamless cross-device experience.

## Architecture
```
PC (EliteDesk) ↔ Phone (Flutter) ↔ Wearable
       ↕               ↕               ↕
    MQTT           WebSocket        Bluetooth
```

## Features

### Push to Phone
- Send text, files, links
- WebSocket relay

### Clipboard Sync
- Real-time clipboard sharing
- Cross-device paste

### File Transfer
- Chunked WebSocket transfer
- "Send this file to my phone"

### Remote Commands
- Authenticated device-to-device
- Phone triggers PC commands

## WebSocket Events
- `mesh_register` — register on mesh
- `mesh_heartbeat` — keepalive
- `push_to_device` — send to specific device
- `clipboard_sync` — sync clipboard
- `transfer_file` — start file transfer

## Related

- [[DATA_STRUCTURE]] — DeviceRegistry schema
- [[API_DOCS]] — device mesh events
- [[Voice Pipeline]] — cross-device voice
- [[Memory Map]] — vault index
