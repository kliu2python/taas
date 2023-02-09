import redis

import datasync.constants as constants
from datasync.conf import CONF
from utils.redis import DataStore

REDIS_CONN = redis.Redis(decode_responses=True, **CONF["redis"])


class TaskCache(DataStore):
    def __init__(self):
        redis_conn = REDIS_CONN
        super().__init__(
            constants.CACHE_KEY,
            redis_conn
        )

