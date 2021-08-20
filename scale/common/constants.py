import os


class RunnerStatus:
    WAITING = "waiting"
    RUNNING = "running"
    CREATED = "created"
    COMPLETED = "completed"


class CaseResult:
    PASS = "passed"
    FAIL = "failed"
    NOTRUN = "notrun"


class SessionStatus:
    STOPPING = "stopping"
    RUNNING = "running"
    COMPLETED = "completed"


CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "config", "controller_config.yaml"
)

RUNNER_STATUS_IDX = {
    RunnerStatus.CREATED: 0,
    RunnerStatus.WAITING: 1,
    RunnerStatus.RUNNING: 2,
    RunnerStatus.COMPLETED: 3
}

REPORT_COMMON_KEYS = [
    "session_id",
    "version",
    "create_time",
    "latest_case",
    "session_status",
    "case_list",
    "clients",
    "_latest_case",
    "loop",
    "should_stop_update_session"
]

REPORT_CLIENT_KEYS = [
    "status",
    "current_case"
]

COMMOM_KEYS_DEF = {
    "session_id": str,
    "version": str,
    "create_time": str,
    "create_timestamp_utc": float,
    "stop_time": str,
    "target_platform": str,
    "result_url": str,
    "session_status": str,
    "latest_case": str,
    "_latest_case": str,
    "case_list": set,
    "clients": set,
    "fail_log": set,
    "run_alias": str,
    "total_passed": int,
    "total_failed": int,
    "latest_passed": int,
    "latest_failed": int,
    "latest_running": int,
    "total_pods": int,
    "pods_running": int,
    "pods_waiting": int,
    "pods_completed": int,
    "pods_created": int,
    "should_stop_update_session": int,
    "loop": int,
    "updated_runners": str,
    "total_commands": int,
    "command_log": list,
    "last_command_log": str
}

CLIENT_KEYS_DEF = {
    "target": str,
    "create_time": str,
    "status": str,
    "current_case": str,
    "passed": int,
    "failed": int
}

SESS_CTRL_KEYS_DEF = {
    "active_session_ids": set,
    "completed_session_ids": set,
    "new_session_queue": set,
    "new_metrics_queue": set
}

WORKER_CTRL_KEYS_DEF = {
    "worker_session_active": set,
    "worker_metrics_active": set,
    "worker_inactive": set,
    "worker_data": set,
    "worker_heartbeat": float,
    "worker_loads": int
}

COMMAND_TASK_MODULE = {
    "task_module": "scale.metrics.command",
    "task_class": "CommandMetrics"
}
SESSION_TASK_MODULE = {
    "task_module": "scale.session.session",
    "task_class": "Session"
}

COMMANDLOG_TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <title>{category} Logs</title>
    <meta http-equiv="Refresh" content="10"> 
  </head>
  <body>
    <div>
     <a href="?ops=download">
        <button type="button">Download</button>
     <a/>
    </div>
    <p>
      {command_logs}
    </p>
  </body>
</html>
"""
