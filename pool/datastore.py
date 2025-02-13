import pool.constants as constants

from utils.logger import get_logger
from utils.redis import DataStore

logger = get_logger()


class PoolDataStore(DataStore):
    def __init__(self, redis_conn):
        super().__init__(
            {
                **constants.DATASTORE_POOL_KEYS
            },
            redis_conn
        )
