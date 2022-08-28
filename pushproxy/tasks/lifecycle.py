import datetime

import prometheus_client
import redis

from pushproxy.common.conf import CONF
from utils.logger import get_logger


LOGGER = get_logger()
KEY_PREFIX = "pushproxy__"
PUSHGATEWAY = CONF.get("push_gateway")
PUSH_PROXY_JOB_SET = f"__PUSHPROXY__jobs"

redis_conf = CONF.get("redis", {})
conn = redis.Redis(
    host=redis_conf.get("server"),
    port=redis_conf.get("port", 6379),
    decode_responses=True
)


def register_alive(job):
    """
    tell server the target is still live, this should not raise exception on
    any condition.
    """
    try:
        conn.set(_get_queue_job_name(job), datetime.datetime.now().timestamp())
        conn.sadd(PUSH_PROXY_JOB_SET, job)
    except Exception as e:
        LOGGER.exception("Error when register alive", exc_info=e)


def _remove_push_gateway(ip, job, grouping_key=None):
    try:
        prometheus_client.delete_from_gateway(ip, job, grouping_key)
    except Exception as e:
        LOGGER.exception("Error when cleanup push gateway", exc_info=e)


def _get_queue_job_name(job):
    return f"{KEY_PREFIX}{job}"


def remove(job):
    LOGGER.info(f"Removing job {job}")
    conn.delete(job)
    job = job.lstrip(KEY_PREFIX)
    _remove_push_gateway(PUSHGATEWAY, job)


def terminate(job):
    try:
        job = _get_queue_job_name(job)
        remove(job)
    except Exception as e:
        LOGGER.exception("Error when remove job", exc_info=e)


def _should_stop_job(job):
    ts = conn.get(job)
    if ts and datetime.datetime.now().timestamp() - float(ts) > 60:
        return True
    return False


def check_job_status(job):
    job = _get_queue_job_name(job)
    status = conn.get(job)
    if status:
        return True
    return False


def house_keeping():
    jobs = conn.keys(f"{KEY_PREFIX}*")
    for job in jobs:
        if _should_stop_job(job):
            remove(job)
