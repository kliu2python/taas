import redis

import monitor.constants as constants
from utils.logger import get_logger
from utils.redis import DataStore

logger = get_logger()


class DataStoreAlert(DataStore):
    def __init__(self, redis_conn):
        super().__init__(
            constants.ALERT_KEYS,
            redis_conn
        )


_redis_conn = redis.Redis(
    host=constants.SYS_CONFIG.config.get("redis_server"),
    port=constants.SYS_CONFIG.config.get("redis_port", 6379),
    decode_responses=True
)
alert_datastore = DataStoreAlert(_redis_conn)
