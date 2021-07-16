import scale.constants as constants
from utils.logger import get_logger
from utils.redis import DataStore

logger = get_logger()


class DataStoreCommon(DataStore):
    def __init__(self, session_id, redis_conn):
        super().__init__(
            constants.COMMOM_KEYS_DEF,
            redis_conn,
            session_id
        )


class DataStoreClient(DataStore):
    def __init__(self, redis_conn):
        super().__init__(
            constants.CLIENT_KEYS_DEF,
            redis_conn
        )


class DataStoreSessionController(DataStore):
    def __init__(self, redis_conn):
        super().__init__(
            constants.SESS_CTRL_KEYS_DEF,
            redis_conn,
            "SESS_CTRL"
        )
