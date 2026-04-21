from dataclasses import asdict

import redis

from .config import RedisConfig, StreamConfig

REDIS = redis.Redis(**asdict(RedisConfig()))

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
