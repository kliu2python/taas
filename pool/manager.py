import os
import json
from threading import Lock
from enum import Enum

import redis

from utils.config import Config
from utils.logger import get_logger
from .datastore import PoolDataStore

config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
logger = get_logger()
global_lock = Lock()
config = Config(config_path).config
redis_server = config.get("redis").get("server")
redis_port = config.get("redis").get("port")
datastore = PoolDataStore(
    redis.Redis(
        host=redis_server,
        port=redis_port,
        decode_responses=True
    )
)


class Status(Enum):
    FREE = "free"
    ASSIGNED = "assigned"


def create_fortitoken_pool(data: dict):
    fortigate_ip = data.get("fortigate_ip")
    fortitoken_pool = []
    if not datastore.exists("fortitoken_pool", fortigate_ip):
        for fortitoken in data.get("fortitokens"):
            fortitoken_status = {
                "sn": fortitoken,
                "status": Status.FREE.value
            }
            fortitoken_pool.append(json.dumps(fortitoken_status))

        datastore.set("fortitoken_pool", fortitoken_pool, fortigate_ip)
        logger.info(f"fortitoken pool {fortitoken_pool} created")
    else:
        logger.info(f"fortitoken pool {fortigate_ip} exists")


def fetch_fortitoken_from_fortitoken_pool(fortitoken_ip: str):

    while True:
        ftk_status = datastore.get("fortitoken_pool", fortitoken_ip)
        if ftk_status:
            for ftk in ftk_status:
                ftk_body = json.loads(ftk)
                if ftk_body.get("status") == Status.FREE.value:
                    available_ftk = {
                        "sn": ftk_body.get("sn"),
                        "status": Status.ASSIGNED.value
                    }
                    datastore.srem("fortitoken_pool", [ftk],
                                   fortitoken_ip)
                    datastore.set("fortitoken_pool",
                                  [json.dumps(available_ftk)],
                                  fortitoken_ip)
                    del available_ftk["status"]

                    return {"res": available_ftk}
            else:
                return {"res": "run out of the resource"}


def release_fortitoken_list(fortitoken: dict):
    ftk_list = fortitoken.get("fortitokens")
    fortitoken_ip = fortitoken.get("fortigate_ip")
    for ftk in ftk_list:
        release_fortitoken(fortitoken_ip, ftk)
        logger.info(f"released fortitoken {ftk}")


def release_fortitoken(fortitoken_ip: str, fortitoken: str):
    ftk_status = {
        "sn": fortitoken,
        "status": Status.ASSIGNED.value
    }

    datastore.srem("fortitoken_pool", [json.dumps(ftk_status)], fortitoken_ip)
    ftk_status["status"] = Status.FREE.value
    datastore.set("fortitoken_pool", [json.dumps(ftk_status)], fortitoken_ip)


def check_pool(fortigate_ip):
    if not datastore.exists("fortitoken_pool", fortigate_ip):
        res = {
            "available": 0,
            "total": 0
        }

    else:
        members = datastore.smembers("fortitoken_pool", fortigate_ip)
        total = len(members)
        amount = 0

        for fortitoken in members:
            fortitoken = json.loads(fortitoken)
            if fortitoken.get("status") == Status.FREE.value:
                amount += 1

        res = {
            "available": amount,
            "total": total
        }

    return res


