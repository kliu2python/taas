# pylint: disable=too-many-arguments
from scale.collector.fil import FilCollector
from scale.collector.ftc import FtcCollector
from scale.common.constants import CONFIG_PATH
from scale.common.variables import ds_common
from utils.metrics import Metrics


PERF_METRICS = {
    "scale_test_cpu_usage": {
        "method": "get_cpu_usage",
        "description": "CPU usage"
    },
    "scale_test_mem_usage": {
        "method": "get_memory_usage",
        "description": "Memory usage"
    },
    "scale_test_sess_count": {
        "method": "get_active_session_count",
        "description": "Active Session Count"
    }
}

class_mapping = {
    "fil": FilCollector,
    "ftc": FtcCollector
}


class _PerfMetrics(Metrics):
    def __init__(
            self,
            ssh_ip,
            ssh_user,
            ssh_password,
            target_platform,
            session_id,
            target_server_ip=None,
            **data
    ):
        if not target_server_ip:
            target_server_ip = ssh_ip
        conn = class_mapping.get(target_platform)(
            ssh_user, ssh_password, ssh_ip, target_server_ip, **data
        )
        job = f"{session_id}-{target_platform}_perf"
        ds_common.set("metrics_running", [job])
        super().__init__(
            PERF_METRICS,
            job,
            conn,
            {"ip": target_server_ip},
            config_path=CONFIG_PATH
        )


class PerfMetrics:
    def __init__(self, **kwargs):
        self.perf_metrics = []
        servers = kwargs.get("servers")
        for server in servers:
            perf_metrics = _PerfMetrics(
                    target_platform=kwargs.get("target_platform"),
                    session_id=kwargs.get("session_id"),
                    **server
            )
            perf_metrics.start_async()
            self.perf_metrics.append(perf_metrics)

    def stop(self):
        return list(map(lambda x: x.stop(), self.perf_metrics))
