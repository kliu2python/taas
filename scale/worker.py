import json
import uuid
from multiprocessing import Process
from time import sleep

import scale.variables as variables
from scale.session import Session
from utils.logger import get_logger

logger = get_logger()


def session_worker():
    worker_id = str(uuid.uuid4())
    variables.ds_control.set("free_workers", [worker_id])
    session = None
    while True:
        try:
            session_data = variables.ds_control.get("worker_data", worker_id)
            if not session and session_data:
                session_data = json.loads(session_data)
                session = Session(**session_data)
            if session and session.completed:
                session = None
                variables.ds_control.delete("worker_data", worker_id)
                variables.ds_control.smove(
                    "using_workers", "free_workers", worker_id
                )
        except Exception as e:
            logger.exception("Error in worker", exc_info=e)
        sleep(5)


if __name__ == "__main__":
    workers = variables.max_workers
    variables.ds_control.delete("free_workers")
    variables.ds_control.delete("using_workers")
    logger.info(f"Starting scaling background {workers} workers")
    processes = []
    for _ in range(workers):
        p = Process(target=session_worker)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
