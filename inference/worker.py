import logging
import socket
import time
import uuid
from dataclasses import asdict

import cv2
import numpy as np
import redis

from common.logging.logging import setup_logging
from common.ml.config import HNSWConfig, InferenceConfig
from common.redis.client import REDIS
from common.redis.config import StreamConfig
from common.schemas.api import EmbeddingTask, InferenceResult
from inference.embedding_generation import EmbeddingGenerator
from inference.search import HNSWSearchTool

setup_logging()
logger = logging.getLogger(__name__)


class InferenceWorker:
    """A worker class for inference."""

    def __init__(self) -> None:
        self.embedding_generator = EmbeddingGenerator(**asdict(InferenceConfig()))
        self.hnsw_search = HNSWSearchTool(**asdict(HNSWConfig()))

        self.hostname = socket.gethostname()
        self.worker_id = f"worker_{self.hostname}_{str(uuid.uuid4())[:8]}"
        self.config = StreamConfig()

        logger.info("Started InferenceWorker '%s'. Listening to %s...", self.worker_id, self.config.stream_name)

    def process(self, embedding_task: EmbeddingTask) -> None:
        """Process the crop task locally."""
        nparr = np.frombuffer(embedding_task.image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite(f"test_{embedding_task.frame_id}.jpg", image)

        if image is None:
            logger.error("Failed to decode image from bytes.")
            return

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        embedding = self.embedding_generator.generate_image_embedding(image_rgb)
        logger.info("Generated embedding of shape %s for frame %s", embedding.shape, embedding_task.frame_id)

        results = self.hnsw_search.search_in_hnsw(embedding)

        inference_result = InferenceResult(frame_id=embedding_task.frame_id, matches=results)
        REDIS.set(f"result:{embedding_task.frame_id}", inference_result.model_dump_json(), ex=300)

        logger.info("Result formatted and pushed into Redis for frame %s", embedding_task.frame_id)

    def worker_loop(self) -> None:
        """Listen to the Redis stream and process crops endlessly using a Consumer Group."""
        while True:
            try:
                # Block and read 1 new message from the stream.
                # ">" means "give me messages that haven't been delivered to other consumers in the group yet"
                response = REDIS.xreadgroup(
                    groupname=self.config.group_name,
                    consumername=self.worker_id,
                    streams={self.config.stream_name: ">"},
                    count=1,
                    block=5000,
                )

                if not response:
                    continue

                _, messages = response[0]

                for message_id, message_data in messages:
                    clean_data = {k.decode("utf-8"): v for k, v in message_data.items()}
                    embedding_task = EmbeddingTask(**clean_data)
                    self.process(embedding_task)
                    REDIS.xack(self.config.stream_name, self.config.group_name, message_id)

            except redis.ConnectionError:
                logger.exception("Redis connection error, retrying...")
                time.sleep(2)
            except Exception:
                logger.exception("Error processing stream: %s")
                time.sleep(1)
