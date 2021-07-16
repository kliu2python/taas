import datetime
import json
import os
import uuid
from copy import deepcopy
from threading import Lock

import redis

import resources.ftc.otp as otp
import resources.fortigate.setup as setup
import utils.dictionary as dictionary
from utils.config import Config
from utils.logger import get_logger
from .constants import TYPE_MAPPING
from .datastore import ResourceDataStore

config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
logger = get_logger()
global_lock = Lock()
config = Config(config_path).config
redis_server = config.get("redis").get("server")
redis_port = config.get("redis").get("port")
datastore = ResourceDataStore(
    redis.Redis(
        host=redis_server,
        port=redis_port,
        decode_responses=True
    )
)


def _is_pool_exist(pool_id):
    curr_active = datastore.get("active_pool")
    if not curr_active or pool_id not in curr_active:
        return False
    return True


def update_pool_list(pool_id, remove=False):
    curr_active = datastore.get("active_pool")
    if not curr_active or (pool_id not in curr_active and not remove):
        datastore.set("active_pool", [pool_id])
    elif curr_active and pool_id in curr_active and remove:
        datastore.redis.srem("active_pool", pool_id)
    else:
        raise ValueError("Invalid operation for update_pool_list")


def create_pool(data):
    datastore.set("worker_data", [json.dumps(data)])
    return "SCHEDULED"


def _update_pool_status(status, pool_id):
    datastore.set("pool_status", status, pool_id)


def get_pool_status(pool_id):
    return datastore.set("pool_status", pool_id)


def do_create_pool(data):
    pool_id = data.get("id")
    if _is_pool_exist(pool_id):
        return "FAIL"
    pool_data = deepcopy(config.get("spec", {}))
    dictionary.deep_update(pool_data, data)
    pool_data = pool_data.get("data")
    pool_type = data.get("type")
    capacity = data.get("capacity")
    pool_data["capacity"] = capacity
    pool_life = data.get("life")
    if pool_life > 0:
        pool_expireation = (
                datetime.datetime.utcnow()
                + datetime.timedelta(minutes=pool_life)
        ).timestamp()
    else:
        pool_expireation = 0
    pool_dict = {
        "pool_id": pool_id,
        "pool_type": pool_type,
        "pool_data": pool_data,
        "pool_status": "Creating",
        "pool_create_time": str(datetime.datetime.utcnow()),
        "pool_expiration": pool_expireation,
        "pool_life": data.get("life"),
        "pool_res_life": data.get("res_life"),
        "pool_capacity": capacity
    }
    datastore.mset(pool_dict, pool_id)
    res_ids = []
    failures = []
    try:
        module = f"resources.{pool_type}"
        class_name = TYPE_MAPPING.get(pool_type)
        res_list, failures = __import__(
            module, fromlist=[class_name]
        ).__getattribute__(
            class_name)().prepare(pool_data)
        res_ids = [str(uuid.uuid4()) for _ in range(len(res_list))]
        datastore.set("pool_res_avaliable", res_ids, pool_id)

        for rid, res in zip(res_ids, res_list):
            dt = datetime.datetime.utcnow()
            dt_exp = (
                    dt + datetime.timedelta(minutes=data.get("res_life"))
            ).timestamp()
            res_dict = {
                "res_id": rid,
                "res_time": str(dt),
                "res_expire": dt_exp,
                "res_data": res
            }
            datastore.mset(res_dict, f"{pool_id}-{rid}")
    except Exception as err:
        logger.exception("Error when execute pool creation", exc_info=err)

    if len(res_ids) == capacity:
        pool_status = "Ready"
    else:
        pool_status = f"Error, failures: {failures}"
    _update_pool_status(pool_status, pool_id)
    update_pool_list(pool_id)
    logger.info(f"Complete Create pool: {pool_id}")


def _clear_pool_data(pool_id):
    keys = datastore.redis.keys(f"{pool_id}*")
    if keys:
        datastore.redis.delete(*keys)


def delete_pool(pool_id):
    if _is_pool_exist(pool_id):
        datastore.set(
            "pool_expiration", datetime.datetime.utcnow().timestamp(), pool_id
        )
        return "SCHEDULED"
    _clear_pool_data(pool_id)
    return f"POOL {pool_id} NOT EXISTS"


def do_delete_pool(pool_id):
    if _is_pool_exist(pool_id):
        if get_pool_statics(pool_id) not in ["Deleting"]:
            _update_pool_status("Deleting", pool_id)
            pool_type = datastore.get("pool_type", pool_id)
            pool_data = datastore.get("pool_data", pool_id)
            module = f"resources.{pool_type}"
            class_name = TYPE_MAPPING.get(pool_type)
            ret = __import__(module, fromlist=[class_name]).__getattribute__(
                class_name)().clean(pool_data)
            _clear_pool_data(pool_id)
            update_pool_list(pool_id, remove=True)
            logger.info(f"Completed delete pool: {pool_id}")
            return ret


def request_resource(pool_id):
    global_lock.acquire()
    try:
        res = datastore.spop("pool_res_avaliable", 1, pool_id)
        if res:
            datastore.set("pool_res_assigned", res, pool_id)
            data = datastore.get("res_data", f"{pool_id}-{res[-1]}")
            data["id"] = res.pop()
        else:
            data = "FAIL, no resource avaliable"
    finally:
        global_lock.release()
    return data


def list_pool():
    return datastore.get("active_pool")


def recycle_resource(pool_id, resource_id):
    if resource_id.lower() in ["all"]:
        count = datastore.scard("pool_res_assigned", pool_id)
        if count > 0:
            assigned = list(datastore.spop("pool_res_assigned", count, pool_id))
            datastore.set("pool_res_avaliable", assigned, pool_id)
        ret = count
    else:
        ret = datastore.smove(
            "pool_res_assigned", "pool_res_avaliable", resource_id, pool_id
        )
    if ret:
        return "SUCCESS"
    return ("FAIL, no resource recycled, "
            "this resource might be already recycled")


def get_pool_statics(pool_id):
    avaliable = datastore.scard("pool_res_avaliable", pool_id)
    used = datastore.scard("pool_res_assigned", pool_id)
    return {"avaliable": avaliable, "used": used}


def show_pool(pool_id):
    ret = {}
    keys = datastore.keys("*", pool_id)
    for key in keys:
        key = datastore.decraft_key(key, pool_id)
        data = datastore.get(key, pool_id)
        ret[key] = data
    return ret


def generate_otp(pool_id, resource_id):
    data = datastore.get("res_data", f"{pool_id}-{resource_id}")
    return otp.OneTimePassword().generate(data.get("seed"))


def fgt_setup(fgt_ip, radius_ip, hostname):
    return setup.setup_config(fgt_ip, radius_ip, hostname, config)
