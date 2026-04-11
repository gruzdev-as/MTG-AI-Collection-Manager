import time
from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel, ConfigDict


@dataclass
class CameraConfig:
    """Configure CameraCapture class hyperparameters and settings."""

    camera_url: str
    max_motion: int
    stable_frames: int
    motion_threshold: float


class FrameMeta(BaseModel):
    """Base Frame Metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    frame_id: str
    timestamp: float = time.time()


class RawFrame(FrameMeta):
    """Raw frame metadata."""

    image: np.ndarray
    width: int
    height: int


class CropTask(BaseModel):
    """Crop Redis Task to process."""

    track_id: str
    frame_id: str
    image_ref: str
    created_at: float = time.time()
