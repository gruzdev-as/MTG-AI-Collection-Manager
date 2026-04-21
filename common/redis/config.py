from dataclasses import dataclass


@dataclass(frozen=True)
class RedisConfig:
    """Configure Redis connection."""

    host: str = "redis"
    port: int = 6379
    decode_responses: bool = False


@dataclass(frozen=True)
class StreamConfig:
    """Configure Redis Streams."""

    stream_name: str = "embedding_stream"
    group_name: str = "inference_group"
