import queue
import threading
import time
import uuid
from dataclasses import asdict

import cv2
import redis

from backend.video.capture import CameraCapture
from backend.video.queues import FrameQueues
from backend.vision.image_processor import ImageProcesser
from common.configs.data_schemas import CropTask, RawFrame, RedisConfig

r = redis.Redis(**asdict(RedisConfig()))


class VideoPipeline:
    """Rule the data flow among different class."""

    def __init__(self, queues: FrameQueues, image_processer: ImageProcesser, camera: CameraCapture) -> None:
        self.queues = queues

        self.image_processer = image_processer
        self.camera = camera
        self.running = False
        self.thread = None

    def start(self) -> None:
        """Call during FastApi lifecycle start."""
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Call during FastApi lifecycle stop."""
        self.running = False

    def _loop(self) -> None:
        """Run the main data pipeline endlessly."""
        while self.running:
            try:
                raw_frame = self.queues.get("frames_raw", timeout=1.0)
            except queue.Empty:
                continue

            processed, contours = self.image_processer.find_big_contours(raw_frame.image)
            is_stable = self.camera.camera_stable_flag

            if is_stable:
                self.camera.pause_event.clear()
                for contour in contours:
                    crop = self.image_processer.crop_warp_image_from_contour(raw_frame.image, contour)

                    crop_task = CropTask(
                        track_id=str(uuid.uuid4()),
                        frame_id=raw_frame.frame_id,
                        image_ref=f"/dev/shm/crop_{uuid.uuid4()}.jpg",
                        created_at=time.time(),
                    )
                    cv2.imwrite(crop_task.image_ref, crop)

                self.camera.camera_stable_flag = False
                self.camera.stable_counter = 0
                self.camera.pause_event.set()

            processed_frame = RawFrame(
                frame_id=raw_frame.frame_id,
                timestamp=raw_frame.timestamp,
                image=processed,
                width=processed.shape[1],
                height=processed.shape[0],
            )

            self.queues.put("frames_processed", processed_frame)
