from enum import Enum


class TASKQueues(Enum):
    DATASYNC_TASK_MAIN = "data_sync_main"
    DATASYNC_TASK_MAIN_REPLY = "data_sync_main_reply"
    DATASYNC_TASK_DR = "data_sync_dr"
    DATASYNC_TASK_DR_REPLY = "data_sync_dr_reply"


class PUSHPROXYQueues(Enum):
    PUSHPROXY_GATEWAY = "pushproxy_queue"


CACHE_KEY = {
    "sync_success_tasks": int,
    "sync_failed_tasks": int,
    "sync_success_clients": int,
    "sync_failed_clients": int,
    "sync_task_cycles": int,
    "running": int
}

# From clients
PROMETHEUS_DATA_SYNC = "ftid_checker_user_sync_status"

# For new metrics
PROMETHEUS_DATA_SYNC_TASKS_SUCCESS = "ftid_sync_task_total_success"
PROMETHEUS_DATA_SYNC_TASKS_FAIL = "ftid_sync_task_total_fail"
PROMETHEUS_DATA_SYNC_CLIENT_SUCCESS = "ftid_sync_client_success"
PROMETHEUS_DATA_SYNC_CLIENT_FAIL = "ftid_sync_client_fail"
PROMETHEUS_DATA_SYNC_CYCLES = "ftid_sync_cycles"
