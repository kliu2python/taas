import os

import redis

from utils.config import Config
from utils.logger import get_logger
from scale.datastore import (
    DataStoreSessionController, DataStoreClient, DataStoreCommon
)
logger = get_logger()

config_path = os.path.join(
    os.path.dirname(__file__), "config", "controller_config.yaml"
)
config = Config(config_path).config
redis_conn = redis.Redis(
    host=config.get("redis_server"),
    port=config.get("redis_port", 6379),
    decode_responses=True
)
ds_control = DataStoreSessionController(redis_conn)
ds_client = DataStoreClient(redis_conn)
ds_common = DataStoreCommon("None", redis_conn)
max_workers = int(os.environ.get("CONCURRENCY", os.cpu_count()))
