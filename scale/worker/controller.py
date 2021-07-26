import sys
from datetime import datetime
from time import sleep

from scale.common.variables import ds_worker, ds_session
from utils.logger import get_logger
from utils.threads import thread

logger = get_logger()


def clear_worker(name):
    try:
        logger.warning(f"Worker {name} dead, removing worker")
        ds_worker.srem("worker_inactive", [name])
        ds_worker.delete("worker_data", name)
        ds_worker.delete("worker_heartbeat", name)
        ds_worker.delete("worker_load", name)
    except Exception as e:
        logger.exception("Error when clean worker", exc_info=e)


def inactivate_worker(name):
    try:
        logger.warning(f"Inactivating worker {name}")
        worker_type = name.split("_")[-2]
        ds_worker.smove(f"worker_{worker_type}_active", "worker_inactive", name)
    except Exception as e:
        logger.exception("Error when inactive worker", exc_info=e)


def activate_worker(name):
    try:
        logger.warning(f"Activating worker {name}")
        worker_type = name.split("_")[-2]
        ds_worker.smove("worker_inactive", f"worker_{worker_type}_active", name)
    except Exception as e:
        logger.exception("Error when active worker", exc_info=e)


def _get_worker_names(worker_type, category="active"):
    ret = []
    if category in ["active"]:
        ret = ds_worker.get(f"worker_{worker_type}_active", default=[])
    elif category in ["inactive"]:
        ret = ds_worker.get("worker_inactive", default=[])
    elif category in ["all"]:
        active = ds_worker.get(f"worker_{worker_type}_active", default=[])
        inactive = ds_worker.get("worker_inactive", default=[])
        active.extend(inactive)
        ret = active
    return ret


@thread
def start_checker():
    while True:
        workers_session = _get_worker_names("session", "active")
        workers_metrics = _get_worker_names("metrics", "active")
        workers = workers_session + workers_metrics
        for worker in workers:
            timestamp_now = datetime.now().timestamp()
            timestamp_worker = ds_worker.get(
                "worker_heartbeat", worker, default=0
            )
            time_delta = timestamp_now - timestamp_worker
            if time_delta >= 10:
                inactivate_worker(worker)

        workers_session = _get_worker_names("session", "inactive")
        workers_metrics = _get_worker_names("metrics", "inactive")
        workers = workers_session + workers_metrics
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


def _get_session_worker(worker_type):
    min_name = None
    min_load = sys.maxsize
    worker_names = _get_worker_names(worker_type)
    for worker in worker_names:
        worker_load = ds_worker.get("worker_loads", worker, default=0)
        if worker_load < min_load:
            min_name = worker
            min_load = worker_load
    return min_name


def assign_task(queue, queue_type):
    new_session_queue = ds_session.exists(queue)
    if new_session_queue:
        new_task = ds_session.spop(queue)[-1]
        if new_task:
            logger.info(f"New Task Received: {new_task}")
            worker = _get_session_worker(queue_type)
            if worker:
                logger.info(f"Assigning to {worker}")
                ds_worker.set("worker_data", [new_task], worker)
            else:
                logger.warning(
                    f"No Worker {queue_type} is ready, will wait and retry"
                )
                ds_session.set(queue, [new_task])


def start_controller():
    logger.info("Starting Worker Controller")
    while True:
        new_session_queue = False
        try:
            assign_task("new_session_queue", "session")
            assign_task("new_metrics_queue", "metrics")
        except Exception as e:
            logger.exception("Error in worker", exc_info=e)
        finally:
            if not new_session_queue:
                sleep(3)


if __name__ == "__main__":
    start_checker()
    start_controller()
