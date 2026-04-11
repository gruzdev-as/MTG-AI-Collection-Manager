import queue
import threading

import cv2

from backend.video.capture import CameraCapture
from backend.video.queues import FrameQueues
from backend.vision.image_processor import ImageProcesser


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
                frame = self.queues.get("frames_raw", timeout=1.0)
            except queue.Empty:
                continue

            processed, contours = self.image_processer.find_big_contours(frame)
            stability = self.camera.similarity_score
            is_stable = self.camera.camera_stable_flag

            if is_stable:
                self.camera.pause_event.clear()
                for contour in contours:
                    crop = self.image_processer.crop_warp_image_from_contour(frame, contour)
                    # TODO @gruzdev-as: Later will be sent to embedding worker
                self.camera.camera_stable_flag = False
                self.camera.stable_counter = 0
                self.camera.pause_event.set()

            # TODO @gruzdev-as: Remove it later
            cv2.putText(
                img=processed,
                text=f"{is_stable}:{stability:.3f}",
                org=(processed.shape[1] // 4, processed.shape[0] // 2),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=2,
                color=(0, 0, 255) if not is_stable else (0, 255, 0),
                thickness=3,
                lineType=cv2.LINE_AA,
            )

            self.queues.put("frames_processed", processed)
