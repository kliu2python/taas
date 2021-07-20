import sys
from datetime import datetime
from time import sleep

from scale.common.variables import ds_worker, ds_control
from utils.logger import get_logger
from utils.threads import thread

logger = get_logger()


def clear_worker(name):
    try:
        logger.warning(f"Worker {name} dead, removing worker")
        ds_worker.srem("worker_active", [name])
        ds_worker.srem("worker_inactive", [name])
        ds_worker.delete("worker_data", name)
        ds_worker.delete("worker_heartbeat", name)
        ds_worker.delete("worker_load", name)
    except Exception as e:
        logger.exception("Error when clean worker", exc_info=e)


def inactivate_worker(name):
    try:
        logger.warning(f"Inactivating worker {name}")
        ds_worker.smove("worker_active", "worker_inactive", name)
    except Exception as e:
        logger.exception("Error when inactive worker", exc_info=e)


def activate_worker(name):
    try:
        logger.warning(f"Activating worker {name}")
        ds_worker.smove("worker_inactive", "worker_active", name)
    except Exception as e:
        logger.exception("Error when active worker", exc_info=e)


def _get_worker_names(category="active"):
    ret = []
    if category in ["active"]:
        ret = ds_worker.get("worker_active", default=[])
    elif category in ["inactive"]:
        ret = ds_worker.get("worker_inactive", default=[])
    elif category in ["all"]:
        active = ds_worker.get("worker_active", default=[])
        inactive = ds_worker.get("worker_inactive", default=[])
        active.extend(inactive)
        ret = active
    return ret


@thread
def start_checker():
    while True:
        workers = _get_worker_names("active")
        for worker in workers:
            timestamp_now = datetime.now().timestamp()
            timestamp_worker = ds_worker.get(
                "worker_heartbeat", worker, default=0
            )
            time_delta = timestamp_now - timestamp_worker
            if time_delta >= 10:
                inactivate_worker(worker)

        workers = _get_worker_names("inactive")
        for worker in workers:
            timestamp_now = datetime.now().timestamp()
            timestamp_worker = ds_worker.get(
                "worker_heartbeat", worker, default=0
            )
            time_delta = timestamp_now - timestamp_worker
            if time_delta > 3600:
                clear_worker(worker)
            elif time_delta < 10:
                activate_worker(worker)
        sleep(5)


def _get_session_worker():
    min_name = None
    min_load = sys.maxsize
    worker_names = _get_worker_names()
    for worker in worker_names:
        worker_load = ds_worker.get("worker_loads", worker, default=0)
        if worker_load < min_load:
            min_name = worker
            min_load = worker_load
    return min_name


def start_controller():
    logger.info("Starting Worker Controller")
    while True:
        new_session_queue = False
        try:
            new_session_queue = ds_control.exists("new_session_queue")
            if new_session_queue:
                new_task = ds_control.spop("new_session_queue")[-1]
                if new_task:
                    logger.info(f"New Task Received: {new_task}")
                    worker = _get_session_worker()
                    if worker:
                        logger.info(f"Assigning to {worker}")
                        ds_worker.set("worker_data", [new_task], worker)
                    else:
                        logger.warning(
                            "No Worker is ready, will wait and retry"
                        )
                        ds_control.set("new_session_queue", [new_task])
        except Exception as e:
            logger.exception("Error in worker", exc_info=e)
        finally:
            if not new_session_queue:
                sleep(3)


if __name__ == "__main__":
    start_checker()
    start_controller()
