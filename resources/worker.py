import datetime
import json
from time import sleep

import resources.manager as manager
from utils.logger import get_logger

logger = get_logger()


def pool_worker():
    logger.info("Starting Pool Worker")
    pool_data = None
    while True:
        try:
            pool_data = manager.datastore.spop("worker_data")
            pools = manager.list_pool()

            if pool_data:
                pool_data = json.loads(pool_data[-1])
                manager.do_create_pool(pool_data)

            if pools:
                for pool_id in pools:
                    if isinstance(pool_id, dict):
                        pool_id = pool_id.get("pool_id")
                    pool_expire = manager.datastore.get(
                        "pool_expiration", pool_id
                    )
                    if pool_expire:
                        to_expire = datetime.datetime.utcnow().timestamp()
                        if to_expire > pool_expire:
                            logger.info(f"Deleting Pool {pool_id}")
                            manager.do_delete_pool(pool_id)
        except Exception as e:
            logger.exception(
                f"Error with data {pool_data}", exc_info=e
            )
        sleep(5)


if __name__ == "__main__":
    pool_worker()
