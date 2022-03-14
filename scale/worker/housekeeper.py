from time import sleep

from scale.common.variables import config
from scale.common.variables import ds_common
from scale.common.variables import ds_session
from utils.logger import get_logger
from utils.metrics import delete_from_gateway

logger = get_logger()


def clear_push_gateway():
    sess_ids = ds_session.sinter(
        "housecleaned_session_id", "completed_session_ids"
    )
    success = True
    if sess_ids:
        for sess in sess_ids:
            jobs = ds_common.get("metrics_running", identifier=sess, default=[])
            for job in jobs:
                try:
                    delete_from_gateway(config.get("pushgateway_ip"), job)
                except Exception as e:
                    logger.exception(
                        f"error when clear push gateway for {job}", exc_info=e
                    )
                    success = False
        if success:
            ds_session.set("housecleaned_session_id", sess_ids)


def run_house_keeping():
    while True:
        clear_push_gateway()
        sleep(30)


if __name__ == "__main__":
    run_house_keeping()
