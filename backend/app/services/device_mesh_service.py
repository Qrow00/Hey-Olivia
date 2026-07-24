import asyncio
import time
import base64
import os
from datetime import datetime, timezone
from typing import Optional


class DeviceMeshService:
    def __init__(self):
        self._devices: dict[str, dict] = {}
        self._clipboard: Optional[str] = None
        self._clipboard_source: Optional[str] = None
        self._clipboard_time: float = 0
        self._file_chunks: dict[str, dict] = {}
        self._message_queue: dict[str, list[dict]] = {}

    def register_device(self, device_id: str, device_info: dict):
        self._devices[device_id] = {
            **device_info,
            "last_seen": time.time(),
            "online": True,
        }

    def unregister_device(self, device_id: str):
        if device_id in self._devices:
            self._devices[device_id]["online"] = False
            self._devices[device_id]["last_seen"] = time.time()

    def heartbeat(self, device_id: str):
        if device_id in self._devices:
            self._devices[device_id]["last_seen"] = time.time()
            self._devices[device_id]["online"] = True

    def get_devices(self) -> list[dict]:
        return [
            {**d, "device_id": did}
            for did, d in self._devices.items()
        ]

    def get_device(self, device_id: str) -> Optional[dict]:
        device = self._devices.get(device_id)
        if device:
            return {**device, "device_id": device_id}
        return None

    def queue_message(self, target_device: str, message: dict):
        if target_device not in self._message_queue:
            self._message_queue[target_device] = []
        self._message_queue[target_device].append({
            **message,
            "queued_at": time.time(),
        })

    def get_queued_messages(self, device_id: str) -> list[dict]:
        messages = self._message_queue.pop(device_id, [])
        return messages

    def update_clipboard(self, content: str, source_device: str):
        self._clipboard = content
        self._clipboard_source = source_device
        self._clipboard_time = time.time()

    def get_clipboard(self) -> Optional[dict]:
        if self._clipboard is None:
            return None
        return {
            "content": self._clipboard,
            "source": self._clipboard_source,
            "timestamp": self._clipboard_time,
        }

    async def prepare_file_transfer(self, file_path: str, target_device: str) -> dict:
        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        transfer_id = f"{target_device}_{int(time.time())}"

        self._file_chunks[transfer_id] = {
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "target_device": target_device,
            "status": "pending",
        }

        return {
            "status": "success",
            "transfer_id": transfer_id,
            "file_name": file_name,
            "file_size": file_size,
        }

    async def read_file_chunk(self, transfer_id: str, offset: int = 0, chunk_size: int = 65536) -> Optional[dict]:
        info = self._file_chunks.get(transfer_id)
        if not info:
            return None

        try:
            with open(info["file_path"], "rb") as f:
                f.seek(offset)
                data = f.read(chunk_size)

            return {
                "data": base64.b64encode(data).decode(),
                "offset": offset,
                "chunk_size": len(data),
                "total_size": info["file_size"],
                "complete": offset + len(data) >= info["file_size"],
            }
        except Exception:
            return None

    def cleanup_transfers(self):
        now = time.time()
        expired = [tid for tid, info in self._file_chunks.items()
                   if now - info.get("created_at", now) > 3600]
        for tid in expired:
            del self._file_chunks[tid]


device_mesh_service = DeviceMeshService()
