import socket
import time
import uuid
from dataclasses import asdict

import cv2
import numpy as np
import redis

from common.ml.config import HNSWConfig, InferenceConfig
from common.redis.client import REDIS
from common.redis.config import StreamConfig
from common.schemas.api import EmbeddingTask, InferenceResult

from .embedding_generation import EmbeddingGenerator
from .search import HNSWSearchTool


def process(embedding_task: EmbeddingTask) -> None:
    """Process the crop task locally."""
    nparr = np.frombuffer(embedding_task.image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imwrite(f"test_{embedding_task.frame_id}.jpg", image)

    if image is None:
        print("Failed to decode image from bytes.")
        return

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    embedding = embedding_generator.generate_image_embedding(image_rgb)
    print(f"Generated embedding of shape {embedding.shape} for frame {embedding_task.frame_id}")

    results = hnsw_search.search_in_hnsw(embedding)

    inference_result = InferenceResult(frame_id=embedding_task.frame_id, **results)
    REDIS.set(f"result:{embedding_task.frame_id}", inference_result.model_dump_json(), ex=300)

    print(f"Result formatted and pushed into Redis for frame {embedding_task.frame_id}")
    return


def worker_loop() -> None:
    """Listen to the Redis stream and process crops endlessly using a Consumer Group."""
    stream_config = StreamConfig()

    # Generate a unique worker ID using the machine's hostname and a UUID snippet
    hostname = socket.gethostname()
    worker_id = f"worker_{hostname}_{str(uuid.uuid4())[:8]}"

    print(f"Started Inference Worker '{worker_id}'. Listening to {stream_config.stream_name}...")

    while True:
        try:
            # Block and read 1 new message from the stream.
            # ">" means "give me messages that haven't been delivered to other consumers in the group yet"
            response = REDIS.xreadgroup(
                groupname=stream_config.group_name,
                consumername=worker_id,
                streams={stream_config.stream_name: ">"},
                count=1,
                block=5000,
            )

            if response:
                _, messages = response[0]
                for message_id, message_data in messages:
                    clean_data = {k.decode("utf-8"): v for k, v in message_data.items()}
                    embedding_task = EmbeddingTask(**clean_data)
                    process(embedding_task)
                    REDIS.xack(stream_config.stream_name, stream_config.group_name, message_id)

        except redis.ConnectionError:  # noqa: PERF203
            print("Redis connection error, retrying...")
            time.sleep(2)
        except Exception as e:  # noqa: BLE001
            print(f"Error processing stream: {e}")
            time.sleep(1)


if __name__ == "__main__":
    embedding_generator = EmbeddingGenerator(**asdict(InferenceConfig()))
    hnsw_search = HNSWSearchTool(**asdict(HNSWConfig()))
    worker_loop()
