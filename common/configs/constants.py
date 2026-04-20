from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import redis


### REDIS
@dataclass(frozen=True)
class RedisConfig:
    """Configure Redis connection."""

    host: str = "redis"
    port: int = 6379
    decode_responses: bool = False


REDIS = redis.Redis(**asdict(RedisConfig()))


### Inference
@dataclass(frozen=True)
class InferenceConfig:
    """Configure inference."""

    model_path: Path = Path("inference/data/CLIP")


### HNSW
@dataclass(frozen=True)
class HNSWConfig:
    """Configure HNSW index."""

    index_path: Path = Path("inference/data/hnsw/hnsw_index_cos.bin")
    index_json_path: Path = Path("inference/data/hnsw/image_metadata.json")
    index_dim: int = 768
    index_space: Literal["cosine", "l2"] = "cosine"
    index_ef: int = 100


### Streams
@dataclass(frozen=True)
class StreamConfig:
    """Configure Redis Streams."""

    stream_name: str = "embedding_stream"
    group_name: str = "inference_group"


def init_redis_streams() -> None:
    """Create consumer groups if they don't exist."""
    config = StreamConfig()
    try:
        REDIS.xgroup_create(config.stream_name, config.group_name, id="0", mkstream=True)
        print(f"Initialized consumer group {config.group_name} for stream: {config.stream_name}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            print(f"Redis error initializing stream: {e}")


# Automatically initialize streams upon importing this constant file
init_redis_streams()
