import queue
import threading
import time
import uuid

import cv2
import numpy as np

from backend.utils.configs import CameraConfig, RawFrame
from backend.video.queues import FrameQueues


class CameraCapture:
    """Responsible for capturing frames from IP webcam and transmit them to queues."""

    def __init__(
        self,
        camera_config: CameraConfig,
        queues: FrameQueues,
        reconnect_delay: float = 2.0,
    ) -> None:
        self.camera_config = camera_config

        self.queues = queues
        self.running: bool = False
        self.camera_stable_flag = False

        self.main_thread: threading.Thread | None = None
        self.stable_thread: threading.Thread | None = None
        self.pause_event = threading.Event()
        self.pause_event.set()

        self.cap: cv2.VideoCapture | None = None
        self.reconnect_delay = reconnect_delay
        self.similarity_score = 0

    def start(self) -> None:
        """Call during FastApi lifecycle start."""
        self.running = True
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.stable_thread = threading.Thread(target=self._is_camera_stable, daemon=True)
        self.main_thread.start()
        self.stable_thread.start()

    def stop(self) -> None:
        """Call during FastApi lifecycle stop."""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def _connect(self) -> cv2.VideoCapture | None:
        """Open the stream from IP."""
        cap = cv2.VideoCapture(self.camera_config.camera_url)
        if not cap.isOpened():
            cap.release()
            return None
        return cap

    def _main_loop(self) -> None:
        """Capture frames endlessly."""
        while self.running:
            self.pause_event.wait()
            if self.cap is None:
                self.cap = self._connect()
                if self.cap is None:
                    time.sleep(self.reconnect_delay)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = None
                time.sleep(self.reconnect_delay)
                continue

            raw_frame = RawFrame(
                frame_id=str(uuid.uuid4()),
                timestamp=time.time(),
                image=frame,
                width=frame.shape[1],
                height=frame.shape[0],
            )

            self.queues.put("frames_raw", raw_frame)
            self.queues.put("frames_stability", raw_frame)

    def _is_camera_stable(self) -> None:
        """Check if camera is stable and the capturing can be start."""
        prev_gray = None
        self.stable_counter = 0
        while self.running:
            self.pause_event.wait()

            try:
                raw_frame = self.queues.get("frames_stability", timeout=1.0)
                frame = raw_frame.image
            except queue.Empty:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            gray = cv2.resize(gray, None, fx=0.1, fy=0.1)
            gray = cv2.GaussianBlur(gray, (9, 9), 0)

            if prev_gray is None:
                prev_gray = gray
                continue

            motion_score = np.mean(cv2.absdiff(prev_gray, gray)).item()

            self.similarity_score = max(0, 1.0 - min(motion_score, self.camera_config.max_motion) / self.camera_config.max_motion)

            if motion_score < self.camera_config.motion_threshold:
                self.stable_counter += 1
            else:
                self.stable_counter = 0

            self.camera_stable_flag = self.stable_counter >= self.camera_config.stable_frames
            prev_gray = gray
