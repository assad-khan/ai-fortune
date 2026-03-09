"""
Palm detection using MediaPipe Tasks HandLandmarker (mediapipe >= 0.10).
Downloads the model file on first run if not present.
"""

from pathlib import Path

import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from PIL import Image

MODEL_PATH = Path(__file__).parent.parent / "hand_landmarker.task"


def _ensure_model() -> str:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"MediaPipe model not found at {MODEL_PATH}. "
            "Run: curl -L 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task' -o hand_landmarker.task"
        )
    return str(MODEL_PATH)


def detect_palm(image: Image.Image) -> tuple[bool, str]:
    """
    Check whether a hand/palm is visible in the image.

    Returns:
        (detected: bool, message: str)
    """
    model_path = _ensure_model()

    img_rgb = np.array(image.convert("RGB"))
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

    base_options = mp_python.BaseOptions(model_asset_path=model_path)
    options = mp_vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.5,
    )

    with mp_vision.HandLandmarker.create_from_options(options) as detector:
        result = detector.detect(mp_image)

    if result.hand_landmarks:
        return True, "Palm detected"

    return False, (
        "No palm detected. Make sure your open hand fills the frame "
        "with your palm facing the camera, in good lighting."
    )
