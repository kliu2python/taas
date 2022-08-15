import motor.motor_asyncio

from utils.logger import get_logger

LOGGER = get_logger()


def _exec(func):
    def wrap(*args, **kwargs):
        return args[0].pump.run_until_complete(func(*args, **kwargs))
    return wrap


class MongoDB:
    def __init__(self, conn_str, default_db=None, default_collection=None):
        self._db_client = motor.motor_asyncio.AsyncIOMotorClient(conn_str)
        self.default_db = default_db
        self.default_collection = default_collection
        self.pump = self._db_client.get_io_loop()

    def _get_collection(self, db, collection):
        if not db:
            db = self.default_db
        if not collection:
            collection = self.default_collection
        return self._db_client[db][collection]

    @_exec
    async def insert(self, document, collection=None, db=None):
        if isinstance(document, dict):
            document = [document]

        coll = self._get_collection(db, collection)
        result = await coll.insert_many(document)
        return result.inserted_id

    @_exec
    async def update(
        self, query, document, collection=None, db=None, upsert=True
    ):
        coll = self._get_collection(db, collection)
        result = await coll.update_one(
            query, {"$set": document}, upsert=upsert
        )
        return result.raw_result["updatedExisting"]

    @_exec
    async def find(self, query, collection=None, db=None):
        ret = []
        coll = self._get_collection(db, collection)
        result = coll.find(query)
        async for res in result:
            res.pop("_id")
            ret.append(res)
        return ret

    @_exec
    async def find_one(self, query, collection=None, db=None):
        coll = self._get_collection(db, collection)
        result = await coll.find_one(query)
        if result:
            result.pop("_id")
        return result

    @_exec
    async def drop_collection(self, db, collection):
        await self._db_client[db].drop_collection(collection)
