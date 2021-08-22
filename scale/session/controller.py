import copy
import datetime
import json
import uuid

import scale.common.constants as constants
from scale.common.variables import (
    ds_session, ds_client, ds_common, redis_conn, config
)
from scale.db.logs import CaseHistory
from scale.db.logs import FailureLog
from utils.dictionary import deep_update
from utils.logger import get_logger

logger = get_logger()


def create_session(data):
    sess_id = data.pop("session_id", None)
    if redis_conn.keys(f"{sess_id}*"):
        date_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M.%f")
        sess_id = f"{sess_id}-{date_time}"
    sess_type = data.pop("session_type", "test")
    data_with_config = copy.deepcopy(config)
    data_with_config = deep_update(data_with_config, data)
    data_with_config["session_id"] = sess_id
    data_with_config.update(constants.SESSION_TASK_MODULE)
    data_with_config_dump = json.dumps(data_with_config)
    if sess_type in ["test"]:
        ds_session.set("new_session_queue", [data_with_config_dump])
    ds_session.set("active_session_ids", [sess_id])
    if data_with_config.get("command_log_targets"):
        data_with_config.update(constants.COMMAND_TASK_MODULE)
        data_with_config_dump = json.dumps(data_with_config)
        ds_session.set("new_metrics_queue", [data_with_config_dump])
    return sess_id


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
        return f"Fail, {e}"


def update_session(data_dict, common_dict=None, session_id=None):
    """
    update session
    common_dict: update shared session data item.
    data_dict: update session data for each runner
    """
    failure_id = None

    def _update_session_data(ds, data, identifier=None):
        nonlocal failure_id
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
                            for c in cases:
                                CaseHistory.create(
                                    session_name=session_id,
                                    case_name=c,
                                    runner_name=identifier,
                                    result=result,
                                    failure_id=failure_id
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
                if k in ["fail_log"]:
                    if v:
                        failure_id = uuid.uuid4()
                        FailureLog.create(id=failure_id, log=v)
                        continue
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
            "active": list(ds_session.smembers("active_session_ids"))
        }
    if session_type in ["completed"]:
        return {
            "completed": list(ds_session.smembers("completed_session_ids"))
        }
    if session_type in ["all"]:
        return {
            "active": list(ds_session.smembers("active_session_ids")),
            "completed": list(ds_session.smembers("completed_session_ids"))
        }

    raise TypeError(f"{session_type} is not supported")


def _move_to_complete(session_id):
    ds_session.smove("active_session_ids", "completed_session_ids", session_id)


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


def stop_session(session_id=None):
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
    free_workers = ds_session.get("free_workers", default=[])
    using_workers = ds_session.get("using_workers", default=[])
    worker_data = {}
    for worker_id in using_workers:
        worker_data[worker_id] = ds_session.get("worker_data", worker_id)

    return {
        "free_workers": len(free_workers),
        "using_workers": len(using_workers),
        "worker_data": worker_data
    }


def _check_session_running(session_id):
    all_active_session = list(ds_session.smembers("active_session_ids"))
    return session_id in all_active_session


def update_runner(data, session_id):
    if _check_session_running(session_id):
        ds_common.set("updated_runners", json.dumps(data), session_id)
        return json.loads(ds_common.get("updated_runners", session_id))
    return f"Session {session_id} is not running"
