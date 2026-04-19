from dataclasses import asdict

import redis

from common.configs.data_schemas import RedisConfig

REDIS = redis.Redis(**asdict(RedisConfig()))
