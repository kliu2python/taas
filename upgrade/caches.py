import redis

import upgrade.constants as constants
from upgrade.conf import CONF
from utils.redis import DataStore


class TaskCache(DataStore):
    def __init__(self):
        redis_conn = redis.Redis(decode_responses=True, **CONF["redis"])
        super().__init__(
            constants.TASK_CACHE_KEYS,
            redis_conn,
            ex=CONF["redis"].get("key_expire", 3600 * 48)
        )


class InfositeCache(DataStore):
    def __init__(self):
        redis_conn = redis.Redis(decode_responses=True, **CONF["redis"])
        super().__init__(constants.INFOSITE_CACHE_KEYS, redis_conn)


class StaticsCache(DataStore):
    def __init__(self):
        redis_conn = redis.Redis(decode_responses=True, **CONF["redis"])
        super().__init__(
            constants.STATICS_CACHE_KEYS,
            redis_conn,
            identifier="__statics"
        )
