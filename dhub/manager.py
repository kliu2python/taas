# pylint: disable=global-statement
import datetime
import json
import threading
import time
import uuid
import os

import redis

import dhub.device.factory as device_factory
from dhub.config import get_config
from utils.config import Config
from dhub.hosts.host import get_host
from dhub.emulator.android import AndroidEmulator as android
from dhub.selenium.node import Node as node

from utils.logger import get_logger
from .datastore import ResourceDataStore

logger = get_logger()
_host = None
_device_slots = {}
_global_lock = threading.Lock()
device_config = get_config("device")
host_config = get_config("host")
global_device_configs = device_config.get_global_configs()
platform_device_configs = device_config.get_platform_configs()
host_config = host_config.get_host_configs()
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
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


def _get_device_slot(platform_id):
    slot_to_assign = None
    slots = _device_slots.get(platform_id)
    lock_acquired = _global_lock.acquire()
    try:
        for slot, item in enumerate(slots):
            if item.get("assign_time") is None:
                slot_to_assign = slot
                refresh_life_span(platform_id, slot)
                break
    except Exception as e:
        print(f"error when assign slot {e}")
    finally:
        if lock_acquired:
            _global_lock.release()
    return slot_to_assign


def _update_slot(platform_id, slot, key=None, value=None):
    global _device_slots
    _device_slots.get(platform_id)[slot][key] = value


def _should_recycle(assign_time: datetime.datetime):
    assign_life_span_minutes = global_device_configs.get("device_life_span")
    dt = datetime.datetime.now() - assign_time
    if dt.seconds // 60 >= assign_life_span_minutes:
        return True
    return False


def _recycle_device_thread_func():
    while True:
        check_recycle_devices()
        time.sleep(_host.config.get("recycle_interval"))


def _recycle_device(platform_id, slot, device=None):
    key_to_clean = {
        "device_obj": None,
        "assign_time": None,
        "request_id": None
    }
    for key, value in key_to_clean.items():
        _update_slot(
            platform_id, slot, key=key, value=value
        )

    if device is not None:
        device.clean_device()


def _start_recycle_thread():
    thread = threading.Thread(target=_recycle_device_thread_func)
    thread.start()
    print("Device recycle thread started")


def _init_device_list():
    global _device_slots
    if not _device_slots:
        for platform in platform_device_configs:
            _device_slots[platform.get("platform_id")] = [
                {
                    "request_id": None,
                    "device_obj": None,
                    "assign_time": None
                } for _ in range(
                    platform.get(
                        "max_devices", host_config.get("device_limits")
                    )
                )
            ]


def _init_host_controller():
    global _host
    _host = get_host(get_config("host").get_host_configs())


def init_device_hub():
    _init_device_list()
    _init_host_controller()
    _start_recycle_thread()


def get_host_obj():
    return _host


def get_device_slot_platform(device_name):
    slot = device_name.split("_")[-1]
    platform_id = device_name.replace(f"_{slot}", "")
    return platform_id, int(slot)


def refresh_life_span(platform_id, slot):
    _update_slot(
        platform_id, slot, key="assign_time", value=datetime.datetime.now()
    )


def recycle_device(platform_id, slot, request_id):
    slot_item = _device_slots.get(platform_id)[slot]
    if request_id in [slot_item.get("request_id")]:
        _recycle_device(platform_id, slot, slot_item.get("device_obj"))
        return "SUCCESS"
    return "Error: Device Evicted"


def check_recycle_devices():
    for platform_id, items in _device_slots.items():
        for slot, item in enumerate(items):
            device_time = item.get("assign_time")
            device = item.get("device_obj")
            if device_time is not None:
                if _should_recycle(device_time):
                    _recycle_device(platform_id, slot, device)


def show_device_slot():
    def default(x):
        if isinstance(x, datetime.datetime):
            return f"{x}"

        return type(x).__qualname__
    try:
        json_dumps = json.dumps(
            _device_slots,
            default=default
        )
        return json.loads(json_dumps)
    except Exception as e:
        return f"{e}"


def assign_device(platform_id):
    last_ip = None
    ip = _host.get_device_host_ip()
    device_info = {}
    while last_ip != ip:
        if ip in [host_config.get("host_ip")]:
            slot = _get_device_slot(platform_id)
            if slot is not None:
                device = device_factory.get_device(
                    device_config.get_config_by_platform_id(platform_id),
                    slot
                )
                device_name = device.get_device()
                if device_name:
                    request_id = f"{uuid.uuid1()}"
                    _update_slot(platform_id, slot, key="device_obj",
                                 value=device)
                    _update_slot(platform_id, slot, key="request_id",
                                 value=request_id)
                    device_info["name"] = device_name
                    device_info["host_ip"] = ip
                    device_info["request_id"] = request_id
                else:
                    print("Failed to get device name, recycling slot")
                    _recycle_device(platform_id, slot, device)
            else:
                print("Failed to get slot")
        else:
            device_info = _host.get_device_remote(ip, platform_id)
            print(f"Trying remove device ip: {ip}")
        if device_info:
            break
        if last_ip is None:
            last_ip = ip
        ip = _host.get_device_host_ip()
    else:
        print("Error: tried all ips. looks no hosts is ready")
    return device_info


def option_device(device_name, session_id, op_method, **kwargs):
    platform_id, slot = get_device_slot_platform(device_name)
    device_assignment = _device_slots.get(platform_id)[slot]
    request_id = device_assignment.get("request_id")
    if request_id == session_id:
        device_obj = device_assignment.get("device_obj")
        return device_obj.option_device(op_method, **kwargs)
    return "Error: Device does not exist"


def launch_emulator(data: dict):
    if data.get("os") == "android":
        session = android(data.get("version"), data.get("dns"))
    else:
        session = None

    name = session.create_pod()
    creator = data.get("creator")
    datastore.set("user_pool", [name], identifier=creator)
    current_time = datetime.datetime.utcnow()
    if data.get("expiration_time") and creator != "automation":
        data_expiration = data.get("expiration_time")
        if data_expiration == -1:
            expiration_time = current_time + datetime.timedelta(days=30)
        elif 0 <= data_expiration <= 3:
            expiration_time = (current_time +
                               datetime.timedelta(days=data_expiration))
        else:
            return ("Please setup the expiration to -1 (max is 30 days) or "
                    "between 0 to 3 days, or remove expiration_time param "
                    "from body (default is 3 days)")
    elif creator == "automation":
        expiration_time = current_time + datetime.timedelta(hours=2)
    else:
        expiration_time = current_time + datetime.timedelta(days=3)
    datastore.set("expiration_time",
                  expiration_time.strftime('%Y-%m-%d %H:%M:%S'),
                  identifier=name)
    datastore.set("pools", [json.dumps({
        "pod_name": name,
        "creator": creator
    })])
    logger.info(f"going to create emulator {str(data)}")
    return name


def do_fetch_pools():
    return datastore.get("pools")


def delete_emulator_worker(data: dict):
    datastore.set("worker_data", [json.dumps(data)])
    pod_name = data.get("pod_name")
    creator = data.get("creator")
    datastore.srem("user_pool", [pod_name], identifier=creator)
    return "working on progress"


def delete_emulator(data: dict):
    if not data.get("pod_name"):
        return {"res": "not pod_name attached, check it again."}
    if not data.get("creator"):
        return {"res": "not creator attached, check it again."}
    pod_name = data.get("pod_name")
    session = android(pod_name=pod_name)
    res = session.delete_pod()
    datastore.delete("pod_info", identifier=pod_name)
    datastore.delete("expiration_time", identifier=pod_name)
    datastore.srem("pools", [json.dumps(data)])
    logger.info(f"The res of delete pod {pod_name} is {res}")
    return res


def check_emulator(pod_name):
    if not pod_name:
        return {"res": "not pod_name attached, check it again."}
    session = android(pod_name=pod_name)
    pod_status = session.check_pod()
    android_version = pod_name.split("-")[0]
    if pod_status not in ["deleted", "unknown"]:
        ports = session.get_ports(pod_name)
        res = {"name": pod_name, "version": android_version,
               "status": pod_status, "vnc_port": ports[0], "adb_port": ports[1]}
    else:
        res = {"name": pod_name, "status": pod_status}
    return res


def list_emulators(user):
    res = []
    pods_str = datastore.get("user_pool", identifier=user)
    if pods_str:
        for pod_name in pods_str:
            pod_details = datastore.get("pod_info", identifier=pod_name)
            if not pod_details or pod_details['status'] not in ['Running',
                                                                'Deleted',
                                                                'deleted']:
                # If the key doesn't exist, fetch the details
                pod_details = check_emulator(pod_name)
                # Store the fetched details in the datastore
                datastore.set("pod_info", pod_details, identifier=pod_name)
            res.append(pod_details)
    return res


def launch_selenium_node(data: dict):
    session = node(node_name=data.get("node_name"), browser=data.get("browser"),
                   version=data.get("version"), portal_ip=data.get("portal_ip"))

    name = session.create_pod()
    logger.info(f"going to create emulator {str(data)}")
    return name


def delete_selenium_node(pod_name: str):
    session = node(pod_name)
    res = session.delete_pod()
    logger.info(f"The res of delete pod {pod_name} is {res}")
    return res


def check_selenium_node(pod_name: str):
    session = node(pod_name)
    res = session.check_selenium_node_status()
    logger.info(f"The res of delete pod {pod_name} is {res}")
    return res


def check_selenium_host_point(pod_name: str, data: dict):
    session = node(pod_name)
    commands = data.get("commands")
    res = session.check_selenium_hostname_point(commands)
    return res
