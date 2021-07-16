import copy
import datetime
import json

import scale.constants as constants
from utils.dictionary import deep_update
from utils.logger import get_logger
from .variables import (
    ds_control, ds_client, ds_common, redis_conn, config
)

logger = get_logger()


def create_session(**data):
    sess_id = data.pop("session_id", None)

    data_with_config = copy.deepcopy(config)
    data_with_config = deep_update(data_with_config, data)
    if redis_conn.keys(f"{sess_id}*"):
        date_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M.%f")
        sess_id = f"{sess_id}-{date_time}"
    data_with_config["session_id"] = sess_id
    if ds_control.get("free_workers"):
        worker_id = ds_control.spop("free_workers")[-1]
        ds_control.set("using_workers", [worker_id])
        data_with_config = json.dumps(data_with_config)
        ds_control.set("worker_data", data_with_config, worker_id)
        ds_control.set("active_session_ids", [sess_id])
        ds_common.set(
            "session_status", constants.SessionStatus.RUNNING, sess_id
        )
        return sess_id
    return "Fail, no free worker to execute"


def read_session(session_id=None, keys: dict = None):
    try:
        common_keys = constants.REPORT_COMMON_KEYS
        client_keys = constants.REPORT_CLIENT_KEYS
        if keys:
            common_k = keys.get("common")
            if common_k:
                common_keys = common_k

            client_k = keys.get("client")
            if client_k:
                client_keys = client_k
        common_values = ds_common.mget(common_keys, session_id)
        clients = common_values.get("clients", [])
        client_values = {}
        for client in clients:
            client_values[client] = ds_client.mget(client_keys, client)
        common_values["data"] = client_values
        return common_values
    except Exception as e:
        logger.exception("Error when try to get data", exc_info=e)
        return "Fail"


def update_session(data_dict, common_dict=None, session_id=None):
    """
    update session
    common_dict: update shared session data item.
    data_dict: update session data for each runner
    """
    def _update_session_data(ds, data, identifier=None):
        for k, v in data.items():
            if v:
                if k in ["case_history"]:
                    for result, cases in v.items():
                        if cases:
                            case_numbers = len(cases)
                            ds_common.incr(
                                f"total_{result}", case_numbers, session_id
                            )
                            ds_client.incr(result, case_numbers, identifier)
                            case_list = [f"{c},{result}" for c in cases]
                            ds_client.set(
                                k, case_list, identifier
                            )
                            last_case = data.get("current_case")
                            if last_case in [
                                ds_common.get("_latest_case", session_id)
                            ]:
                                ds_common.incr(
                                    f"latest_{result}", len(cases), session_id
                                )
                    continue
                if k in ["status"]:
                    last_status = ds_client.get(
                        "status", identifier
                    )
                    if last_status and last_status != v:
                        ds_common.decr(
                            f"pods_{last_status}", 1, session_id
                        )
                        ds_common.incr(f"pods_{v}", 1, session_id)
                    else:
                        ds_common.incr("total_pods", 1, session_id)
                    ds_common.set(
                        "clients", [identifier], session_id
                    )
                ds.set(k, v, identifier)

    session_status = ds_common.get("session_status", session_id)
    if session_status not in [constants.SessionStatus.RUNNING]:
        return f"Fail, session {session_id} is {session_status}"

    if not (
            ds_common.get("should_stop_update_session", session_id)
            and not ds_common.get("loop", session_id)
    ):
        if common_dict:
            _update_session_data(ds_common, common_dict, session_id)

        if data_dict:
            target = data_dict.get("target")
            if not ds_client.exists("create_time", target):
                client_data = {
                    "create_time": str(datetime.datetime.now()),
                    "status": constants.RunnerStatus.CREATED,
                    "current_case": "N/A",
                    "passed": 0,
                    "failed": 0
                }
                ds_client.mset(client_data, target)
            _update_session_data(ds_client, data_dict, target)
    return "SUCCESS"


def list_session(session_type="all"):
    if session_type in ["active"]:
        return {
            "active": list(ds_control.smembers("active_session_ids"))
        }
    if session_type in ["completed"]:
        return {
            "completed": list(ds_control.smembers("completed_session_ids"))
        }
    if session_type in ["all"]:
        return {
            "active": list(ds_control.smembers("active_session_ids")),
            "completed": list(ds_control.smembers("completed_session_ids"))
        }

    raise TypeError(f"{session_type} is not supported")


def _move_to_complete(session_id):
    ds_control.smove("active_session_ids", "completed_session_ids", session_id)
    _save_session()


def _save_session():
    redis_conn.save()


def _get_report_url(session_id):
    start_time = round(
        ds_common.get("create_timestamp_utc", session_id), 3
    ) * 1000
    end_time = round(datetime.datetime.now().timestamp(), 3) * 1000
    platform = ds_common.get("target_platform", session_id)
    url = config.get("grafana_dash_board", {}).get(platform)
    if url:
        return (f"{url}&from={start_time}&to={end_time}"
                f"&var-session_id={session_id}")


def quit_session(session_id=None):
    try:
        session_status = ds_common.get("session_status", session_id)
        if session_status in [constants.SessionStatus.RUNNING]:
            ds_common.set(
                "session_status", constants.SessionStatus.STOPPING, session_id
            )
            _move_to_complete(session_id)
            msg = _get_report_url(session_id)
            ds_common.set("result_url", "msg", session_id)
        else:
            msg = f"Fail, session '{session_id}' is {session_status}"
    except Exception as e:
        raise e
    return msg


def list_worker():
    free_workers = ds_control.get("free_workers", default=[])
    using_workers = ds_control.get("using_workers", default=[])
    worker_data = {}
    for worker_id in using_workers:
        worker_data[worker_id] = ds_control.get("worker_data", worker_id)

    return {
        "free_workers": len(free_workers),
        "using_workers": len(using_workers),
        "worker_data": worker_data
    }


def _check_session_running(session_id):
    all_active_session = list(ds_control.smembers("active_session_ids"))
    return session_id in all_active_session


def update_runner(data, session_id):
    if _check_session_running(session_id):
        ds_common.set("updated_runners", json.dumps(data), session_id)
        return json.loads(ds_common.get("updated_runners", session_id))
    return f"Session {session_id} is not running"
