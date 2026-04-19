import time
from dataclasses import dataclass

from pydantic import BaseModel


class EmbeddingTask(BaseModel):
    """Crop Redis Task to process."""

    frame_id: str
    image_ref: str
    created_at: float = time.time()


@dataclass(frozen=True)
class RedisConfig:
    """Configure Redis connection."""

    host: str = "redis"
    port: int = 6379
    decode_responses: bool = True
