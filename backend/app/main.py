import asyncio
import os
from contextlib import asynccontextmanager
from queue import Queue

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.utils.configs import CameraConfig
from backend.video.capture import CameraCapture
from backend.video.pipeline import VideoPipeline
from backend.video.queues import FrameQueues
from backend.vision.image_processor import ImageProcesser


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
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

    app.state.queues = FrameQueues(queue_dict)
    app.state.image_processer = ImageProcesser()
    app.state.capture = CameraCapture(config, app.state.queues)
    app.state.pipeline = VideoPipeline(
        queues=app.state.queues,
        image_processer=app.state.image_processer,
        camera=app.state.capture,
    )

    app.state.capture.start()
    app.state.pipeline.start()

    yield

    app.state.capture.stop()
    app.state.pipeline.stop()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/stream")
async def stream1(websocket: WebSocket) -> None:
    """Streaming processed video frames to frontend."""
    await websocket.accept()
    try:
        while True:
            frame_data = await asyncio.to_thread(websocket.app.state.queues.get, "frames_processed")
            frame = frame_data.image
            _, frame = cv2.imencode(".jpg", frame)
            await websocket.send_bytes(frame.tobytes())
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket stream.")
    except RuntimeError as e:
        print(f"Error streaming video: {e}")
