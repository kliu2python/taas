import datetime
import json
from time import sleep

import dhub.manager as manager
from utils.logger import get_logger

logger = get_logger()


def pool_worker():
    logger.info("Starting Pool Worker")
    device_info = None
    emulator_data = None
    selenium_name = None
    pod_pool = None
    while True:
        try:
            if not device_info:
                device_info = manager.datastore.spop("worker_data")
                pod_pool = manager.do_fetch_pools()

            if device_info:
                for device in device_info:
                    if '{' in device:
                        emulator_data = json.loads(device)
                        manager.delete_emulator(emulator_data)
                        emulator_data = None
                    else:
                        selenium_name = device
                        manager.do_delete_selenium_node(selenium_name)
                        selenium_name = None
                    device_info.remove(device)
            if pod_pool:
                for pod in pod_pool:
                    pod_data = json.loads(pod)
                    pod_id = pod_data["pod_name"]
                    expiration_time = manager.datastore.get(
                        "expiration_time", pod_id)
                    current_time = datetime.datetime.utcnow()
                    if expiration_time:
                        exp_time = datetime.datetime.strptime(
                            expiration_time, '%Y-%m-%d %H:%M:%S'
                        )
                        if current_time > exp_time:
                            logger.info(f"Deleting Pool {pod_id}")
                            if len(pod_data) > 1:
                                manager.delete_emulator(pod_data)
                            else:
                                manager.delete_selenium_node(pod_id)

        except Exception as e:
            if selenium_name:
                device_info.append(selenium_name)
            if emulator_data:
                device_info.append(emulator_data)
            logger.exception(
                f"Error with data {device_info}", exc_info=e
            )
        sleep(5)


if __name__ == "__main__":
    pool_worker()
