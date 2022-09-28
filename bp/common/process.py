import datetime
import os
import time

import yaml

from bp.common.versions import RESOURCE_MAPPING
from bp.common import bp as bps
from utils.logger import get_logger
from bp.Analysis import analyzer

logger = get_logger("clear")


def call_bp(data):
    wait_time = 60
    host = data["bp_ip"]
    bp_case = data["bp_case"]
    bp_group = data["bp_group"]
    api_version = RESOURCE_MAPPING[host]
    user = data["user"]
    password = data["password"]
    bp = bps.BpClient(host, user, password, api_version)
    bp.login()
    run_id = None
    logger.info("start common")

    while wait_time > 0:
        try:
            run_id = bp.run_case(bp_case, bp_group)
            logger.info("Run start")
            break
        except Exception as e:
            logger.exception(f"run start fail", exc_info=e)
            wait_time -= 10
            if wait_time <= 0:
                raise e
            logger.info("Wait 60 seconds and retry")
            time.sleep(10)

    logger.info(f"BP Run started for case:{bp_case}, run id: {run_id}")
    return run_id


def report_analysis(data, runid):
    AUTOMATION_DIR = os.path.dirname(__file__)
    REPORT_DIR = os.path.join(
        AUTOMATION_DIR, "benchmark_report"
    )
    os.makedirs(REPORT_DIR, exist_ok=True)
    host = data["bp_ip"]
    bp_case = data["bp_case"]
    report_type = data["report_type"]
    user = data["user"]
    password = data["password"]
    working_directory = os.getcwd()
    file_path = os.path.join(working_directory, "bp")
    file_path = os.path.join(file_path, "report_def.yaml")
    with open(file_path) as F:
        report_def = yaml.safe_load(F)

    report_file_csv = os.path.join(
        REPORT_DIR, f"{runid}_{bp_case}.csv"
    )
    api_version = RESOURCE_MAPPING[host]
    bp = bps.BpClient(host, user, password, api_version)
    bp.login()
    bp.get_report(report_file_csv, runid, report_format="csv",
                  section_ids="7", timeout=600)
    if os.path.exists(report_file_csv):
        result = analyzer.Analyzer(report_file_csv, report_type,
                                   report_def.get("report_def")).analyze()
        return result
    raise Exception


def stop_run(data, run_id):
    host = data["bp_ip"]
    api_version = RESOURCE_MAPPING[host]
    user = data["user"]
    password = data["password"]
    duration = data["duration"]
    bp = bps.BpClient(host, user, password, api_version)
    bp.login()
    start_datetime = datetime.datetime.now()
    end_datetime = start_datetime + datetime.timedelta(minutes=duration)
    print("Waiting bp case running Minutes:", duration)
    while datetime.datetime.now() < end_datetime:
        status = {}
        try:
            status = bp.get_running_status(run_id)
        except Exception as e:
            logger.exception("Error when get realtime status",
                             exc_info=e)
        logger.info(f"\n{status}")
        time.sleep(10)
    logger.info("stopping BP run")
    bp.stop_run(run_id)
    bp.logout()
    return "stop"
