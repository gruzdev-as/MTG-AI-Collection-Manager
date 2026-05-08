import logging
from dataclasses import asdict

from redis import Redis
from redis.exceptions import ResponseError

from common.logging.logging import setup_logging
from common.redis.config import RedisConfig, StreamConfig

setup_logging()
REDIS = Redis(**asdict(RedisConfig()))
logger = logging.getLogger(__name__)


def init_redis_streams() -> None:
    """Create consumer groups if they don't exist."""
    config = StreamConfig()
    try:
        REDIS.xgroup_create(config.stream_name, config.group_name, id="0", mkstream=True)
        logger.info("Initialized consumer group %s for stream: %s", config.group_name, config.stream_name)
    except ResponseError as e:
        if "BUSYGROUP" not in str(e):
            logger.exception("Redis error initializing stream:")


# Automatically initialize streams upon importing this constant file
init_redis_streams()
