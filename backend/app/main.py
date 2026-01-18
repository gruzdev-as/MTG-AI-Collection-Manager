import asyncio
import base64
import functools
import os
import threading
from contextlib import asynccontextmanager
from queue import Empty, Queue

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket
from utils.configs import CameraConfig
from video.capture import CameraCapture
from video.pipeline import VideoPipeline
from video.queues import FrameQueues
from vision.image_processor import ImageProcesser

config = CameraConfig(
    camera_url=os.getenv("CAMERA_URL", "0"),
    max_motion=10,
    motion_threshold=2,
    stable_frames=30,
)

queue_dict = {
    "frames_raw": Queue(maxsize=1),
    "frames_processed": Queue(maxsize=1),
    "frames_stability": Queue(maxsize=1),
}

queues = FrameQueues(queue_dict)
image_processer = ImageProcesser()
capture = CameraCapture(config, queues)
pipeline = VideoPipeline(queues=queues, image_processer=image_processer, camera=capture)


@asynccontextmanager
async def lifespan(app: FastAPI):
    capture.start()
    pipeline.start()
    yield
    capture.stop()
    pipeline.stop()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/stream")
async def stream1(websocket: WebSocket) -> np.ndarray:
    """Streaming processed video frames to frontend."""
    await websocket.accept()
    while True:
        frame = queues.get("frames_processed")
        _, frame = cv2.imencode(".jpg", frame)
        await websocket.send_bytes(frame.tobytes())
