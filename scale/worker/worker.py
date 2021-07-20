import json
import platform
import uuid
from datetime import datetime
from time import sleep

import scale.common.constants as constants
from scale.common.variables import ds_worker, ds_control, ds_common
from scale.session.session import Session
from utils.logger import get_logger
from utils.threads import thread

logger = get_logger()
sessions = []
appendex = str(uuid.uuid4())[:8]
host_name = platform.node()
worker_id = f"{host_name}__{appendex}"


def register_worker():
    ds_worker.set("worker_active", [worker_id])


def update_worker():
    timestamp = datetime.now().timestamp()
    ds_worker.set("worker_heartbeat", timestamp, worker_id)
    for session in sessions:
        if session.completed:
            sessions.remove(session)
            ds_worker.decr("worker_loads", 1, worker_id)


@thread
def start_session(session_data):
    session = Session(**session_data)
    sessions.append(session)


def start_worker():
    logger.info(f"Starting Worker {worker_id}")
    ds_worker.set("worker_loads", 0, worker_id)
    while True:
        try:
            update_worker()
            session_data = None
            if ds_worker.exists("worker_data", worker_id):
                session_data = ds_worker.spop(
                    "worker_data", identifier=worker_id
                )[-1]
            if session_data:
                session_data = json.loads(session_data)
                logger.info(f"Starting session {session_data}")
                start_session(session_data)
                sess_id = session_data["session_id"]
                ds_control.set("active_session_ids", [sess_id])
                ds_common.set(
                    "session_status", constants.SessionStatus.RUNNING, sess_id
                )
                ds_worker.incr("worker_loads", 1, worker_id)
        except Exception as e:
            logger.exception("Error in worker", exc_info=e)
        sleep(3)


if __name__ == "__main__":
    register_worker()
    start_worker()
