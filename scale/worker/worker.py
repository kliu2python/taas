import json
import os
import platform
import uuid
from datetime import datetime
from multiprocessing import Process, Event
from time import sleep

import scale.common.constants as constants
from scale.common.variables import ds_worker, ds_common
from utils.logger import get_logger
from utils.threads import thread

logger = get_logger()
tasks = {}
tasks_events = {}
appendex = str(uuid.uuid4())[:8]
host_name = platform.node()
worker_type = os.environ.get("WORKER_TYPE", "session")
worker_id = f"{host_name}_{worker_type}_{appendex}"


def register_worker():
    if not ds_worker.sismember(f"worker_{worker_type}_active", worker_id):
        ds_worker.set(f"worker_{worker_type}_active", [worker_id])
        ds_worker.set("worker_loads", len(tasks), worker_id)


def update_worker():
    register_worker()
    timestamp = datetime.now().timestamp()
    ds_worker.set("worker_heartbeat", timestamp, worker_id)


def run_task(task_data):
    def task_process(e: Event, task_method, data):
        task_obj = task_method(data)
        e.wait()
        if hasattr(task_obj, "stop"):
            task_obj.stop()

    task_data = json.loads(task_data)
    task_id = task_data["session_id"]
    logger.info(f"Starting task id: {task_id}\n data: {task_data}")
    worker_module = task_data.pop("task_module")
    worker_class = task_data.pop("task_class")
    worker_task = __import__(
        worker_module, fromlist=[worker_class]
    ).__getattribute__(worker_class)
    event = Event()
    task_proc = Process(
        target=task_process, args=(event, worker_task, task_data)
    )
    task_proc.start()
    tasks[task_id] = task_proc
    tasks_events[task_id] = event


@thread
def stop_task():
    while True:
        id_to_remove = []
        for task_id, task_proc in tasks.items():
            if (
                ds_common.get("session_status", task_id)
                in [constants.SessionStatus.STOPPING,
                    constants.SessionStatus.COMPLETED]
            ):
                try:
                    if task_proc.is_alive():
                        task_event = tasks_events.pop(task_id)
                        if task_event:
                            task_event.set()
                        retry = 30
                        while retry > 0:
                            if not task_proc.is_alive():
                                logger.info("task process exited")
                                break
                            retry -= 1
                            if retry <= 0:
                                logger.warning(
                                    f"task {task_id} is not self stopped, "
                                    f"killing now"
                                )
                                task_proc.terminate()
                                if not task_proc.is_alive():
                                    logger.info("task process killed")
                            sleep(2)
                except Exception as e:
                    logger.exception(f"Error stop task {task_id}", exc_info=e)
                finally:
                    id_to_remove.append(task_id)
                    ds_worker.decr("worker_loads", 1, worker_id)
        for task_id in id_to_remove:
            tasks.pop(task_id)
        sleep(3)


def start_worker():
    logger.info(f"Starting {worker_type} Worker, id: {worker_id}")
    stop_task()
    while True:
        try:
            update_worker()
            task_data = None
            if ds_worker.exists("worker_data", worker_id):
                task_data = ds_worker.spop(
                    "worker_data", identifier=worker_id
                )[-1]
            if task_data:
                run_task(task_data)
                ds_worker.incr("worker_loads", 1, worker_id)
        except Exception as e:
            logger.exception("Error in worker", exc_info=e)
        sleep(3)


if __name__ == "__main__":
    start_worker()
