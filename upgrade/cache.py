import redis

from upgrade.conf import CONF
from upgrade.constants import TASK_KEYS
from utils.redis import DataStore


class Cache(DataStore):
    def __init__(self):
        redis_conn = redis.Redis(decode_responses=True, **CONF["redis"])
        super().__init__(
            TASK_KEYS, redis_conn, ex=CONF["redis"].get("key_expire", 3600 * 48)
        )
