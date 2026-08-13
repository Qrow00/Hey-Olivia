"""face_embed_util - preprocessing + embedding helpers for MobileFaceNet-style models.

Expected model: 112x112 RGB input, normalized to [-1, 1], outputs a
feature vector (typically 128/192/512-d). Detached so heavy deps (cv2/ort)
are only imported on demand.
"""

from typing import List


def face_embedding(session, face_bgr) -> List[float]:
    """Compute embedding vector for a detected face crop (BGR numpy array)."""
    import cv2
    import numpy as np

    face = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    face = cv2.resize(face, (112, 112)).astype(np.float32)
    face = (face - 127.5) / 128.0
    face = np.expand_dims(face.transpose(2, 0, 1), axis=0)
    outputs = session.run(None, {session.get_inputs()[0].name: face})
    emb = np.asarray(outputs[0]).flatten()
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm
    return emb.tolist()
