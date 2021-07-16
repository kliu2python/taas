import resources.constants as constants

from utils.logger import get_logger
from utils.redis import DataStore

logger = get_logger()


class ResourceDataStore(DataStore):
    def __init__(self, redis_conn):
        super().__init__(
            {
                **constants.DATASTORE_RESOURCE_KEYS,
                **constants.DATASTORE_POOL_KEYS,
                **constants.DATASTORE_WORKER_KEYS
            },
            redis_conn
        )
