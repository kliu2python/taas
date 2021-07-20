import scale.common.constants as constants
from utils.metrics import Metrics

SESS_METRICS = {
    "scale_test_sess_created_runner_count": {
        "method": "get_total_created_runner",
        "description": "Runners Just Created"
    },
    "scale_test_sess_running_runner_count": {
        "method": "get_runner_count_by_status",
        "args": {"status": constants.RunnerStatus.RUNNING},
        "description": "Runners Started Running Cases"
    },
    "scale_test_sess_waiting_runner_count": {
        "method": "get_runner_count_by_status",
        "args": {"status": constants.RunnerStatus.WAITING},
        "description": "Runners waiting for start case message"
    },
    "scale_test_sess_completed_runner_count": {
        "method": "get_runner_count_by_status",
        "args": {"status": constants.RunnerStatus.COMPLETED},
        "description": "Runners completed count"
    },
    "scale_test_sess_expected_runner_count": {
        "method": "get_expected_runner_count",
        "description": "Total Test runners expected"
    },
    "scale_test_sess_total_case_count": {
        "method": "get_total_case_count",
        "description": "Total Test case numbers"
    },
    "scale_test_sess_latest_case_running_count": {
        "method": "get_latest_case_running_count",
        "description": "Total latest case running count"
    },
    "scale_test_sess_latest_case_pass_count": {
        "method": "get_case_result_count_latest_case",
        "args": {"expected_result": constants.CaseResult.PASS},
        "description": "Total Test case passed on latest case count"
    },
    "scale_test_sess_latest_case_fail_count": {
        "method": "get_case_result_count_latest_case",
        "args": {"expected_result": constants.CaseResult.FAIL},
        "description": "Total Test case failed on latest case count"
    },
    "scale_test_sess_total_case_pass_count": {
        "method": "get_case_result_count_total",
        "args": {"expected_result": constants.CaseResult.PASS},
        "description": "Total Test case failed on all tests count"
    },
    "scale_test_sess_total_case_fail_count": {
        "method": "get_case_result_count_total",
        "args": {"expected_result": constants.CaseResult.FAIL},
        "description": "Total Test case failed on all tests count"
    },
    "scale_test_sess_completed_cases_count": {
        "method": "get_total_complete_case_count",
        "description": "Total Test case count completed"
    },
    "scale_test_sess_pods_status": {
        "method": "get_session_pods_status",
        "labels": ["podname", "currentcase", "casepassed", "casefailed"],
        "description": "Total Test case count completed"
    }
}


class SessionMetrics(Metrics):
    def __init__(self, session, **data):
        super().__init__(
            SESS_METRICS,
            f"{session.session_id}-{data.get('target_platform', '')}"
            f"_sess_metrics",
            session,
            config_path=constants.CONFIG_PATH
        )
        self.start_async()
