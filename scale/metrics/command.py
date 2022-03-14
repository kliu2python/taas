# pylint: disable=too-many-arguments
from scale.collector.fgt import FgtCollector
from scale.common.constants import CONFIG_PATH
from scale.common.variables import ds_common
from utils.metrics import Metrics

CLASS_MAPPING = {
    "fgt": FgtCollector
}


class CommandMetrics:
    def __init__(self, data):
        """
        command_log_targets format:
        [
            {
                "type": "type1", // required, for now only fgt,
                "category": "crashlog", // crash log has default command for fgt
                "interval_seconds": 10, // check interval in seconds
                "param1": "xxxx", //  init parmameter for collector class
                "param2": "xxxx",
                ......
            },
            {
                "type": "type2", // required, for now only fgt,
                "category": "general", // command log.
                "param1": "xxxx", //  init parmameter for collector class
                "param2": "xxxx",
                ......
            }
        ]

        type: only support fgt, default is fgt
        category: crashlog or general, general is default
        remove_dup: if you want to remove dup logs, default is False

        e.g.:
        [
            {
                "type": "fgt",
                "category": "crashlog",
                "ssh_user": "admin",
                "ssh_password": "fortinet",
                "ssh_ip": "10.160.16.19"
            },
            {
                "type": "fgt",
                "category": "general",
                "remove_dup": true // if you want to remove duplicate log
                "commands": [
                    "config vdom",
                    "edit root",
                    "get vpn ssl monitor"
                ]
                "ssh_user": "admin",
                "ssh_password": "fortinet",
                "ssh_ip": "10.160.16.19",
                "interval_seconds": 10
            }
        ]
        """
        self.command_metrics = []
        target_devices = data.get("command_log_targets", [])
        session_id = data.get("session_id")
        for target in target_devices:
            device_type = target.pop("type", "fgt")
            category = target.get("category")
            if category in ["crashlog"]:
                metrics = {
                    "scale_total_crash_count": {
                        "method": "get_total_commands",
                        "description": "get crashes count",
                        "labels": ["device", "ip"],
                    }
                }
                target["remove_dup"] = True
            elif category in ["general"]:
                metrics = {
                    "scale_total_command_count": {
                        "method": "get_total_commands",
                        "description": "get total commands collected",
                        "labels": ["device", "ip"],
                    }
                }
            else:
                raise ValueError("category value should be crashlog or general")
            conn = CLASS_MAPPING.get(device_type)(ds_common, session_id, target)
            job = f"{device_type}_{target.get('category')}-{session_id}"
            metrics = Metrics(
                metrics,
                job,
                conn,
                config_path=CONFIG_PATH,
                interval_seconds=target.get("interval_seconds")
            )
            ds_common.set("metrics_running", [job])
            metrics.start_async()
            self.command_metrics.append(metrics)

    def stop(self):
        return list(map(lambda x: x.stop(), self.command_metrics))
