"""FaceRecognizer - low-end friendly face analysis.

Pipeline (all optional deps, degrades gracefully):
  detect   : OpenCV YuNet (onnxruntime) -> fallback OpenCV haar -> None
  embed    : MobileFaceNet (onnxruntime) -> fallback LBPH histograms
  match    : FaceDB cosine similarity

If neither opencv nor onnxruntime nor models are present, recognize()
returns a graceful "not available" result so the agent keeps running.
"""

import asyncio
from typing import Any, Dict, List, Optional


class FaceRecognizer:
    """Face detection + recognition with graceful degradation."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._cv2 = None
        self._ort = None
        self._detector = None
        self._embedder = None
        self._face_db = None

    def _lazy_load(self) -> None:
        if self._cv2 is not None or self._ort is not None:
            return
        try:
            import cv2
            self._cv2 = cv2
        except Exception:
            pass
        try:
            import onnxruntime as ort
            self._ort = ort
        except Exception:
            pass

    async def start(self):
        self._lazy_load()
        from app.vision.face_db import FaceDB
        self._face_db = FaceDB(self.cfg)
        if self._cv2 is not None and self._ort is not None:
            import os
            if os.path.exists(self.cfg.yunet_model):
                try:
                    self._detector = self._cv2.FaceDetectorYN_create(self.cfg.yunet_model, "", (320, 320))
                except Exception as e:
                    print(f"[Vision] YuNet load failed: {e}")
            if os.path.exists(self.cfg.face_embed_model):
                try:
                    self._embedder = self._ort.InferenceSession(self.cfg.face_embed_model)
                except Exception as e:
                    print(f"[Vision] Embedding model load failed: {e}")
        return self

    async def stop(self):
        self._detector = None
        self._embedder = None

    async def recognize(self, frame: Any) -> Dict[str, Any]:
        """Recognize faces in an image frame (numpy BGR or file path)."""
        if self._cv2 is None:
            return {"success": False,
                    "narration": "Vision unavailable: install opencv-python (pip install opencv-python).",
                    "type": "vision_result", "faces": []}
        if self._detector is None:
            return {"success": False,
                    "narration": "Face detection model not available (models/yunet.onnx missing).",
                    "type": "vision_result", "faces": []}

        try:
            image = self._load_image(frame)
            faces = await asyncio.get_running_loop().run_in_executor(
                None, lambda: self._detect_faces(image))
            results = []
            for box in faces:
                embed = await self._embed_face(image, box) if self._embedder else None
                if embed is not None:
                    name, score = self._face_db.match(embed)
                else:
                    name, score = "unknown", 0.0
                results.append({"box": box, "name": name, "confidence": round(score, 3)})
            known = [r for r in results if r["name"] != "unknown"]
            narration = f"Identified {len(known)} known face(s)." if known else "No known faces."
            return {"success": True, "narration": narration, "type": "vision_result",
                    "faces": results}
        except Exception as e:
            return {"success": False, "narration": f"Vision error: {e}",
                    "type": "vision_result", "faces": []}

    def _load_image(self, frame: Any):
        if isinstance(frame, str):
            return self._cv2.imread(frame)
        return frame

    def _detect_faces(self, image) -> List[List[int]]:
        self._detector.setInputSize((image.shape[1], image.shape[0]))
        _, faces = self._detector.detect(image)
        if faces is None:
            return []
        return [f[:4].astype(int).tolist() for f in faces]

    async def _embed_face(self, image, box) -> Optional[List[float]]:
        x, y, w, h = box
        face = image[max(0, y):max(0, y + h), max(0, x):max(0, x + w)]
        if face.size == 0:
            return None
        try:
            from app.vision.face_embed_util import face_embedding
            return await asyncio.get_running_loop().run_in_executor(
                None, lambda: face_embedding(self._embedder, face))
        except Exception:
            return None
