import datetime
import json
from time import sleep

import dhub.manager as manager
from utils.logger import get_logger

logger = get_logger()


def pool_worker():
    logger.info("Starting Pool Worker")
    emulator_info = None
    while True:
        try:
            emulator_info = manager.datastore.spop("worker_data")
            pod_pool = manager.do_fetch_pools()

            if emulator_info:
                emulator_data = json.loads(emulator_info[-1])
                manager.delete_emulator(emulator_data)
            if pod_pool:
                for pod in pod_pool:
                    pod_data = json.loads(pod)
                    pod_id = pod_data["pod_id"]
                    expiration_time = manager.datastore.get(
                        "expiration_time", pod_id)
                    current_time = datetime.datetime.utcnow()
                    if expiration_time:
                        exp_time = datetime.datetime.strptime(
                            expiration_time, '%Y-%m-%d %H:%M:%S'
                        )
                        if current_time > exp_time:
                            logger.info(f"Deleting Pool {pod_id}")
                            manager.delete_emulator(pod_data)

        except Exception as e:
            logger.exception(
                f"Error with data {emulator_info}", exc_info=e
            )
        sleep(5)


if __name__ == "__main__":
    pool_worker()
