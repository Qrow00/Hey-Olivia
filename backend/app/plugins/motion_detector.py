from app.plugins.base import DevicePlugin, PluginInfo
from dataclasses import dataclass


class MotionDetectorPlugin(DevicePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id="motion_detector",
            name="Motion Detector",
            version="1.0.0",
            description="Detects motion in camera feeds using frame differencing",
            author="J.A.R.V.I.S.",
            capabilities=["motion_detection", "motion_alerts"],
        )

    async def initialize(self, config: dict = None) -> bool:
        self._threshold = config.get("threshold", 0.05) if config else 0.05
        self._cooldown = config.get("cooldown", 5) if config else 5
        self._last_motion: dict[str, float] = {}
        self._motion_history: dict[str, list] = {}
        print(f"MotionDetector initialized (threshold={self._threshold})")
        return True

    async def shutdown(self) -> bool:
        print("MotionDetector shutdown")
        return True

    async def handle_command(self, command: str, params: dict) -> dict:
        if command == "detect":
            return await self._detect_motion(params)
        elif command == "get_history":
            return self._get_history(params.get("camera_id", ""))
        elif command == "set_threshold":
            self._threshold = params.get("threshold", 0.05)
            return {"status": "updated", "threshold": self._threshold}
        elif command == "get_config":
            return {"threshold": self._threshold, "cooldown": self._cooldown}
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}

    async def _detect_motion(self, params: dict) -> dict:
        camera_id = params.get("camera_id", "")
        frame1 = params.get("frame1")
        frame2 = params.get("frame2")

        if not frame1 or not frame2:
            return {"status": "error", "message": "Two frames required for motion detection"}

        try:
            import cv2
            import numpy as np
            import base64
            import time

            img1 = cv2.imdecode(
                np.frombuffer(base64.b64decode(frame1), np.uint8),
                cv2.IMREAD_COLOR
            )
            img2 = cv2.imdecode(
                np.frombuffer(base64.b64decode(frame2), np.uint8),
                cv2.IMREAD_COLOR
            )

            if img1 is None or img2 is None:
                return {"status": "error", "message": "Invalid frame data"}

            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
            gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

            diff = cv2.absdiff(gray1, gray2)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

            motion_pixels = cv2.countNonZero(thresh)
            total_pixels = thresh.shape[0] * thresh.shape[1]
            motion_ratio = motion_pixels / total_pixels

            has_motion = motion_ratio > self._threshold

            if has_motion:
                now = time.time()
                last = self._last_motion.get(camera_id, 0)
                if now - last > self._cooldown:
                    self._last_motion[camera_id] = now
                    if camera_id not in self._motion_history:
                        self._motion_history[camera_id] = []
                    self._motion_history[camera_id].append({
                        "timestamp": now,
                        "ratio": motion_ratio,
                    })
                    if len(self._motion_history[camera_id]) > 100:
                        self._motion_history[camera_id] = self._motion_history[camera_id][-50:]

            return {
                "status": "success",
                "camera_id": camera_id,
                "motion_detected": has_motion,
                "motion_ratio": round(motion_ratio, 4),
                "threshold": self._threshold,
            }

        except ImportError:
            return {"status": "error", "message": "OpenCV not installed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_history(self, camera_id: str) -> dict:
        history = self._motion_history.get(camera_id, [])
        return {
            "camera_id": camera_id,
            "events": history[-20:],
            "total_events": len(history),
        }
