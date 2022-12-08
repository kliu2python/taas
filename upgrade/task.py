import datetime
import os
import uuid
from time import sleep

from upgrade.conf import CONF
from upgrade.caches import TaskCache
from upgrade.constants import TYPE_MAPPING
from utils.celery import make_celery
from utils.logger import get_logger

cache = TaskCache()
celery = make_celery("updater", CONF["celery"])
logger = get_logger()


def get_updater(platform):
    mod_path = f"upgrade.{platform}.updater"
    class_name = TYPE_MAPPING.get(platform)
    updater = __import__(mod_path, fromlist=[class_name]).__getattribute__(
        class_name
    )
    return updater


def _prepare(req_id, data):
    dst_dir = os.path.join(CONF["ftp"]["dst_dir"], req_id)

    os.makedirs(dst_dir, exist_ok=True)

    data["dst_dir"] = dst_dir
    return data


def _wait_task_lock(req_id, data):
    logger.info("Wait existing task finish")
    while True:
        lock = check_wait(data)
        if lock:
            sleep(5)
        else:
            set_task_lock(req_id, data)
            logger.info(f"Depended task {lock} completed, starting new task")
            break


def _handle_exception(req_id, data):
    cache.set("status", "fail", req_id)
    cache.set("task_data", data, req_id)


@celery.task(time_limit=3600)
def do_update(req_id, data, wait):
    retry = CONF.get("task", {}).get("retry", 1)
    error = None
    while retry > 0:
        try:
            if wait:
                _wait_task_lock(req_id, data)
            data = _prepare(req_id, data)
            cache.set("status", "in progress", req_id)
            cache.set("task_data", {"input": data}, req_id)
            updater = get_updater(data.get("platform", "fos"))
            access_info = data["device_access"]
            result, status = updater(**access_info).update(req_id, data)
            data.update(result)
            if status:
                cache.set("task_data", data, req_id)
                cache.set("status", "completed", req_id)
                break
            raise Exception("task fail, please check result")
        except Exception as e:
            error = e
            _handle_exception(req_id, data)
            retry -= 1
        finally:
            unlock_task_lock(data)
            if error:
                raise error


def _get_host_ip(data):
    host = data.get("device_access", {}).get("host")
    if host:
        return host
    raise Exception("target ip is required for upgrade")


def get_task_lock(data):
    host = _get_host_ip(data)
    return cache.get("task_lock", host)


def set_task_lock(req_id, data):
    host = _get_host_ip(data)
    cache.set("task_lock", req_id, host, expire=3600)


def unlock_task_lock(data):
    host = _get_host_ip(data)
    cache.delete("task_lock", host)


def get_task_status(req_id):
    return cache.get("status", req_id)


def check_wait(data):
    running_task = get_task_lock(data)
    if running_task:
        status = get_task_status(running_task)
        return status in ["in progress", "pending"]
    return False


def schedule(data):
    req_id = str(uuid.uuid4())
    ret = {"upgrade_id": req_id}
    try:
        wait = False
        if not data.get("force", False):
            wait = check_wait(data)
        if not wait:
            set_task_lock(req_id, data)

        data["time"] = str(datetime.datetime.now())
        cache.set("task_data", data, req_id)
        task = do_update.delay(req_id, data, wait)
        cache.set("task_id", task.id, req_id)
        cache.set("status", "pending", req_id)
    except Exception as e:
        cache.set("status", "fail", req_id)
        _handle_exception(req_id, data)
        ret["error"] = f"Error when schedule job {req_id}: {str(e)}"
        logger.exception(f"Error when schedule job {req_id}", exc_info=e)
    return ret


def get_result(req_id):
    return {
        "status": cache.get("status", req_id),
        "upgrade_id": req_id,
        "info": cache.get("task_data", req_id)
    }


def revoke_task(req_id):
    task_id = cache.get("task_id", req_id)
    celery.control.revoke(task_id)
    data = cache.get("task_data", req_id)
    cache.set("status", "cancelled", req_id)
    ip = data["device_access"]["host"]
    cache.delete("task_lock", ip)
