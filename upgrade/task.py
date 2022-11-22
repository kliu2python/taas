import os
import uuid

from upgrade.conf import CONF
from upgrade.cache import Cache
from upgrade.constants import TYPE_MAPPING
from utils.celery import make_celery

cache = Cache()
celery = make_celery("updater", CONF["celery"])


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


@celery.task
def do_update(req_id, data):
    retry = CONF.get("task", {}).get("retry", 1)
    while retry > 0:
        try:
            data = _prepare(req_id, data)
            cache.set("status", "in progress", req_id)
            cache.set("task_data", {"input": data}, req_id)
            updater = get_updater(data.get("platform"))
            access_info = data["device_access"]
            file, version = updater(**access_info).update(req_id, data)
            data["used_file"] = file
            data["current_version"] = version
            cache.set("task_data", data, req_id)
            cache.set("status", "completed", req_id)
            break
        except Exception as e:
            cache.set("status", f"failed", req_id)
            data["error"] = f"{e}"
            cache.set("task_data", data, req_id)
            retry -= 1
            if retry <= 0:
                raise e


def update(data):
    req_id = str(uuid.uuid4())
    task = do_update.delay(req_id, data)
    cache.set("task_id", task.id, req_id)
    return req_id


def get_result(req_id):
    return {
        "status": cache.get("status", req_id),
        "upgrade_id": req_id,
        "info": cache.get("task_data", req_id)
    }


def revoke_task(req_id):
    task_id = cache.get("task_id", req_id)
    celery.control.revoke(task_id)
