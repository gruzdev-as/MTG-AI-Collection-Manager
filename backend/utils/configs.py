from dataclasses import dataclass


@dataclass
class CameraConfig:
    """Configure CameraCapture class hyperparameters and settings."""

    camera_url: str
    max_motion: int
    stable_frames: int
    motion_threshold: float
