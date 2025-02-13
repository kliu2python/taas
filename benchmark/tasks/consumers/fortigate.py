import json

import benchmark.services.reporting as service
from benchmark.common.conf import CONF
from benchmark.common.pushproxy import PushGateway
from benchmark.parser.fortigate import FortigateParser
from benchmark.tasks.lifecycle import register_alive
from benchmark.tasks.lifecycle import terminate
from utils.logger import get_logger

LOGGER = get_logger()
IDX_MAPPING = {"-1": "dataplane", "-2": "MBD"}
PUSH_GATEWAY = CONF.get("push_gateway")


def upload_to_push_proxy(data, job, time=None):
    """
    counter value with labels:
    [
        {
            labels: {
                label_name1: label1,
                label_name2: label2
            }
            value: xxx
        }
    ]
    """
    try:
        push_data = []
        for d in data:
            idx = d["idx"]
            idx = IDX_MAPPING.get(idx, idx)
            counter = d["counter"]
            value = d["value"]
            labels = None
            if "dpdk-cpu" in counter:
                category = f"benchmark_{counter.replace('-', '_')}_percent"
                v_type = "cpu"
            elif "cpu" in counter:
                category = "benchmark_cpu_percent"
                v_type = "cpu"
            elif "memory" in counter:
                category = "benchmark_memory_percent"
                v_type = "memory"
            elif "dpdk-drop-engine" in counter:
                category = "benchmark_dpdk_drop_engine"
                v_type = "drop"
                labels = {
                    f"{v_type}": f"{idx}",
                }
            elif "dpdk-drop-vnp" in counter:
                category = "benchmark_dpdk_drop_vnp"
                v_type = "drop"
                labels = {
                    f"{v_type}": f"{idx}",
                }
            elif "chassie_sync" in counter:
                category = "fortigate_chassie_sync_status"
                v_type = "chassie_sync"
            else:
                raise TypeError(f"Counter type {counter} is not supported")
            to_append = {
                "category": category,
                "labels": {
                    f"{v_type}": f"{v_type}-{idx}",
                },
                "value": float(value),
                "description": "bp benchmark perf metrics"
            }
            if labels:
                to_append["labels"] = labels
            push_data.append(to_append)
        
        push_proxy = PushGateway(PUSH_GATEWAY, job)
        push_proxy.push(push_data, time)
    except Exception as e:
        LOGGER.exception("", exc_info=e)


def upload_to_db(data, job_name, build_id, case_name, exec_time, bmrk_time):
    for d in data:
        d["job_name"] = job_name
        d["build_id"] = build_id
        d["case_name"] = case_name
        d["exec_time"] = exec_time
        d["bmrk_time"] = bmrk_time
        msg, code = service.CounterApi.create(d)
        if code != 201:
            LOGGER.error(f"Debug,Failed to upload data to db: {msg}")


def consume_data(message):
    try:
        data = json.loads(message)
        push_job_name = data.get("push_job_name")
        status = data.get("status")

        if status in ["terminated"]:
            terminate(push_job_name)
        else:
            time = data.pop("time")
            exec_time = data.pop("exec_time")
            cmd_out = data.get("data")
            job_name = data.get("job_name")
            build_id = data.get("build_id")
            case_name = data.get("case_name")
            bmrk_time = data.get("bmrk_time")

            metrics = FortigateParser.parse(cmd_out)

            upload_to_push_proxy(metrics, push_job_name, time)
            upload_to_db(metrics, job_name, build_id, case_name, exec_time,
                         bmrk_time)

            register_alive(push_job_name)
        LOGGER.info("finished the decoding of message")
    except Exception as e:
        LOGGER.exception(f"{e} happened during decoding the message")
        raise e
