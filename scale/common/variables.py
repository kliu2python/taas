import os

import redis

from utils.cassandra import register_connection
from utils.config import Config
from utils.logger import get_logger
from scale.common.cache import (
    DataStoreSessionController,
    DataStoreClient,
    DataStoreCommon,
    DataStoreWorkerController
)

logger = get_logger()

config_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "config",
    "controller_config.yaml"
)
config = Config(config_path).config
redis_conn = redis.Redis(
    host=config.get("redis_server"),
    port=config.get("redis_port", 6379),
    decode_responses=True
)
ds_session = DataStoreSessionController(redis_conn)
ds_worker = DataStoreWorkerController(redis_conn)
ds_client = DataStoreClient(redis_conn)
ds_common = DataStoreCommon("None", redis_conn)
db = config.get("db", {})
datacenter = db.pop("dc", "dc1")
if db:
    cass_session = register_connection(name="taas", **db)
