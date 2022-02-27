# pylint: disable=no-name-in-module, too-many-instance-attributes

import datetime
import json
import os
from time import sleep

import requests
import redis
import yaml

import scale.common.constants as constants
from utils.logger import get_logger
from utils.threads import thread, ThreadsManager
from scale.common.cache import DataStoreClient, DataStoreCommon
from scale.common.notifier import Notifier
from scale.common.variables import config
from scale.metrics.perf import PerfMetrics
from scale.metrics.session import SessionMetrics
from scale.metrics.elasticsearch import ElasticSearchMetrics


logger = get_logger()
KUBE_FILE_PATH = os.path.dirname(os.path.dirname(__file__))


class Session:
    """
    Session for a collection of runners.

    It has Data store for storing the test data, data will be flushed to disk
    for now, this will be add to DB later.
    data format:
    {
        session_id: "xxxxx"
        create_time: "xxxxxx",
        case_list: [],
        clients: {
            "hostname1": {
                create_time: "xxxxxx",
                status: "waiting", or "running", "created"
                current_case: "xxx",
                case_history: [
                    ["Case1", "PASS"],
                    ["Case2", "FAIL"]
                ]
            },
            "hostname2": {
                create_time: "xxxxxx",
                status: "waitting" or "running" or "created" or others
                current_case: "xxx",
                case_history: [
                    ["Case1", "PASS"],
                    ["Case2", "FAIL"]
            }
        }
    }
    """
    def __init__(self, data):
        self.completed = False
        self.pods_adjust_momentum = data.get("pods_adjust_momentum", 1)
        self.session_id = data.get("session_id")
        self.config_download_server = config.get(
            "config_download_server", "10.160.50.118:8889"
        )
        self.runner_image = data.get("runner_image")
        self.launch_command = data.get("launch_command")
        self.launch_args = data.get("launch_args")
        self.namespace = data.get("namespace", self.session_id).lower()
        self.redis_conn = redis.Redis(
            host=data.get("redis_server"),
            port=data.get("redis_port", 6379),
            decode_responses=True
        )
        self.data_store_common = DataStoreCommon(
            self.session_id, self.redis_conn
        )
        self.data_store_client = DataStoreClient(self.redis_conn)
        session_data = {
            "session_id": self.session_id,
            "version": data.get("version", ""),
            "create_time": str(
                datetime.datetime.now()
            ),
            "create_timestamp_utc": datetime.datetime.now().timestamp(),
            "run_alias": data.get("alias_name", "No"),
            "session_status": constants.SessionStatus.RUNNING,
            "target_platform": data.get("target_platform"),
            "total_passed": 0,
            "total_failed": 0,
            "latest_passed": 0,
            "latest_failed": 0,
            "latest_running": 0,
            "total_pods": 0,
            "pods_running": 0,
            "pods_waiting": 0,
            "pods_completed": 0,
            "pods_created": 0,
            "total_commands": 0
        }
        self.data_store_common.mset(session_data)
        self.data_store_common.set("loop", 1)
        self._total_created_runner = 0
        self._next_case_id = 0
        self.runner_count = 0
        self.runner_count_range = None
        self.data_store_common.set("should_stop_update_session", 0)
        self._pods_collector_running = False
        self.last_case = False
        self._pods_metrics = {}
        self.sess_metrics = SessionMetrics(self, **data)
        self.perf_metrics = None
        if data.get("servers"):
            self.perf_metrics = PerfMetrics(**data)
        self.elastic_search = None
        if data.get("elastic_search"):
            self.elastic_search = ElasticSearchMetrics(
                self.session_id, **data
            )
        self.notifier = Notifier(
            self,
            before_callback=self._before_notify_callback,
            after_callback=self._after_notifiy_callback,
            **data
        )
        self._runners_updated = False
        self._set_runner_count(data.get("runner_count"))
        self.cid_pods_metrics = self._start_pods_metrics_collector()
        self.deployment_config = data.get(
            "deployment_config", "runner_deployment.yaml"
        )
        self.data_store_common.set(
            "session_status", constants.SessionStatus.RUNNING, self.session_id
        )
        self._apply_runner_deployment(self.runner_count, redeploy=True)
        # TODO: Investigate dynamic runner
        # self._create_runners(self.runner_count, redeploy=True)

    def _set_runner_count(self, runner_count):
        if isinstance(runner_count, list):
            if (
                len(runner_count) == 2
                and runner_count[0] >= 0
                and runner_count[1] >= 0
            ):
                self.runner_count_range = runner_count
                self.runner_count = runner_count[0]
                if runner_count[0] - runner_count[1] > 0:
                    self.pods_adjust_momentum *= -1
            else:
                raise ValueError("Runner count range list must have two values")
            self.data_store_common.set("loop", 1)
        elif isinstance(runner_count, int):
            if runner_count > 0:
                self.runner_count = runner_count
        else:
            raise ValueError(
                f"runner_count: {runner_count} is not in valid data value "
                f"type or range"
            )

    def _before_notify_callback(self):
        if self.last_case:
            case_list = self._get_case_list()
            self._next_case_id = 0
            if case_list:
                self.data_store_common.set("_latest_case", case_list[0])
            self.data_store_common.set("latest_passed", 0)
            self.data_store_common.set("latest_failed", 0)
            self._handle_session_end()
            self.last_case = False

    def _after_notifiy_callback(self):
        try:
            case_list = self._get_case_list()
            if case_list:
                if self._next_case_id < len(case_list):
                    latest_case = case_list[
                        min(self._next_case_id, len(case_list)-1)
                    ]
                    self.data_store_common.set("_latest_case", latest_case)
                    if self._next_case_id == len(case_list) - 1:
                        logger.info("loop_end = True")
                        self.last_case = True
                    self._next_case_id += 1
                self.data_store_common.set(
                    "latest_case", self.data_store_common.get("_latest_case")
                )
        except Exception as e:
            logger.exception("Error when update_latest_case", exc_info=e)

    def save(self):
        self.redis_conn.save()

    def stop(self):
        self.data_store_common.set("should_stop_update_session", 1)
        self.data_store_common.set("stop_time", str(datetime.datetime.now()))
        self.notifier.stop()
        self._stop_metrics()
        self._delete_runner_deployment()
        try:
            ThreadsManager().wait_for_complete([self.cid_pods_metrics])
        except Exception as e:
            logger.info("Error when wait for thread stopping", exc_info=e)
        self.data_store_common.set(
            "session_status", constants.SessionStatus.COMPLETED
        )
        self.completed = True

    def _apply_runner_deployment(self, runners, redeploy=False, wait=False):
        kube_file = os.path.join(
            KUBE_FILE_PATH, f"kube_file_{self.session_id}.yaml"
        )
        if os.path.exists(kube_file):
            os.remove(kube_file)

        data = requests.get(
            f"http://{self.config_download_server}/"
            f"{self.deployment_config}"
        )
        with open(kube_file, "w") as FILE:
            kube_content = list(
                yaml.safe_load_all(data.content.decode("utf-8"))
            )
            for content in kube_content:
                if content.get("kind") in ["Namespace"]:
                    if self.namespace:
                        content["metadata"]["name"] = self.namespace
                if content.get("kind") in ["Deployment"]:
                    if self.namespace:
                        content["metadata"]["namespace"] = self.namespace
                    content["spec"]["replicas"] = runners
                    containers = content["spec"]["template"]["spec"][
                        "containers"]
                    for c in containers:
                        env = c.get("env", [])
                        env.append(
                            {"name": "SESSION_ID", "value": self.session_id}
                        )
                        c["env"] = env
                        if self.runner_image:
                            c["image"] = self.runner_image
                        if self.launch_command:
                            c["command"] = self.launch_command
                        if self.launch_args:
                            c["args"] = self.launch_args
                    break
            yaml.dump_all(kube_content, FILE)

        if redeploy:
            self._delete_runner_deployment()
        os.system(f"kubectl apply -f {kube_file}")
        if wait:
            os.system(f"kubectl apply -f {kube_file} --wait")

    def _create_runners(self, runners, redeploy=False, wait=False):
        total_runners = runners
        expected_runners = 0
        if redeploy:
            self._delete_runner_deployment()
            redeploy = False
        while total_runners > 0:
            changed_runners = 50
            if total_runners <= changed_runners:
                changed_runners = total_runners

            expected_runners += changed_runners
            self._apply_runner_deployment(expected_runners, redeploy, wait)
            timeout = 1200
            while timeout > 0:
                if self.data_store_common.get(
                        "session_status",
                        default=constants.SessionStatus.RUNNING
                ) in [
                    constants.SessionStatus.RUNNING
                ]:
                    curr_runners = self.data_store_common.get(
                        "pods_waiting", default=0
                    )
                    logger.info(
                        f"Curr runner: {curr_runners}, "
                        f"Exp runner :{expected_runners}")
                    if curr_runners == expected_runners:
                        logger.info(f"Created {changed_runners} runners")
                        total_runners -= changed_runners
                        break
                    sleep(10)
                    timeout -= 10
                else:
                    logger.info("User abort run, stop creating runner")
                    return
            if timeout <= 0:
                logger.error("Can not deploy Runners, now clearning deployed")
                self._delete_runner_deployment()
                return

    def _delete_runner_deployment(self):
        try:
            kube_file = os.path.join(
                KUBE_FILE_PATH, f"kube_file_{self.session_id}.yaml"
            )
            os.system(f"kubectl delete -f {kube_file} --now=true --wait=false")
        except Exception as e:
            logger.exception(
                "Error when delete kube deployment, please check on k8s",
                exc_info=e
            )

    def _handle_updated_runners(self):
        try:
            new_runners = self.data_store_common.get("updated_runners")
            if new_runners:
                new_runners_data = json.loads(new_runners)
                self.pods_adjust_momentum = new_runners_data.get("momentum", 1)
                self._set_runner_count(new_runners_data.get("runners"))
                self.data_store_common.delete("updated_runners")
                self._runners_updated = True
        except Exception as e:
            logger.exception("Error when update runners count", exc_info=e)

    def _handle_session_end(self):
        if not self.data_store_common.get("loop"):
            self.data_store_common.set("should_stop_update_session", 1)
        else:
            # update test pods count if we are setting set step changing pods.
            self._handle_updated_runners()
            if self.runner_count_range or self._runners_updated:
                curr_runner_count = self.runner_count
                if self._runners_updated:
                    self._runners_updated = False
                else:
                    self.runner_count += self.pods_adjust_momentum
                    if self.pods_adjust_momentum > 0:
                        self.runner_count = min(
                            self.runner_count, self.runner_count_range[1]
                        )
                    else:
                        self.runner_count = max(
                            self.runner_count, self.runner_count_range[1]
                        )
                if curr_runner_count != self.runner_count:
                    logger.info(
                        f"Adjusting Running pods to {self.runner_count}"
                    )
                    self._apply_runner_deployment(self.runner_count, wait=True)
                    # TODO: Move back later
                    # self._create_runners(self.runner_count, wait=True)
                else:
                    logger.info(
                        "Reached target runners number,"
                        "no change for runners count"
                    )

    @thread
    def _start_pods_metrics_collector(self):
        self._pods_collector_running = True
        while self._pods_collector_running:
            try:
                self._collect_pods_metics()
                sleep(4)
            except Exception as e:
                logger.exception(
                    "Error when collect pods metrics, retry in 5s",
                    exc_info=e
                )

    def _collect_pods_metics(self):
        pods_status_list = []
        clients = self.data_store_common.get("clients", default=[])
        self._total_created_runner = len(clients)

        for client in clients:
            # collect latest case results count
            pod = {
                "labels": {
                    "podname": client,
                    "currentcase": self.data_store_client.get(
                        "current_case", client
                    ),
                    "casepassed": self.data_store_client.get("passed", client),
                    "casefailed": self.data_store_client.get("failed", client)
                },
                "value": constants.RUNNER_STATUS_IDX.get(
                    self.data_store_client.get("status", client)
                )
            }
            pods_status_list.append(pod)

        # check if we need notify notifier it is the last case
        if (
                self.data_store_common.get("should_stop_update_session")
                and not self.data_store_common.get("loop")
        ):
            self.notifier.set_last_case()

        self._pods_metrics["pods_status_list"] = pods_status_list

    def _stop_metrics(self):
        self.sess_metrics.stop()
        if self.perf_metrics:
            self.perf_metrics.stop()
        if self.elastic_search:
            self.elastic_search.stop()
        self._pods_collector_running = False

    def _get_case_list(self):
        return self.data_store_common.get("case_list", default=[])

    def get_expected_runner_count(self):
        return self.runner_count

    def get_runner_count_by_status(self, status):
        return self.data_store_common.get(f"pods_{status}", default=0)

    def get_total_case_count(self):
        return len(self._get_case_list())

    def get_latest_case_running_count(self):
        return self.data_store_common.get("latest_running", default=0)

    def get_current_running_case_name(self):
        return self.data_store_common.get("latest_case", default="")

    def get_total_created_runner(self):
        return self._total_created_runner

    def get_total_complete_case_count(self):
        return min(self._next_case_id, len(self._get_case_list()))

    def get_case_result_count_latest_case(self, expected_result):
        return self.data_store_common.get(
            f"latest_{expected_result}", default=0
        )

    def get_case_result_count_total(self, expected_result):
        return self.data_store_common.get(
            f"total_{expected_result}", default=0
        )

    def get_session_pods_status(self):
        return self._pods_metrics.get("pods_status_list", [])
