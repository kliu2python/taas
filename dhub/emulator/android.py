import os
import traceback
import uuid
from time import sleep
import telnetlib

import yaml

from kubernetes import (
    client,
    config
)
from kubernetes.stream import stream

from dhub.constants import ADB_KEYCODES
from dhub.resources.api_level_comparison_table import (
    android_api_to_version
)
from utils.logger import get_logger

logger = get_logger()
WORK_DIC = os.getcwd()
NAMESPACE = "emulator-cloud"
VNC_PORT = 6901
ABD_PORT = 4723


class AndroidEmulator:
    def __init__(self, version=None, dns=None, pod_name=None):
        self.config = None
        self.pod_name = pod_name
        self.vnc_node_port = VNC_PORT
        self.adb_node_port = ABD_PORT
        self.unique_name = None
        self.model_name = None
        self.model_location = None
        self.version = version
        self.dns = dns
        self.api_client = None
        self.__enter__()

    def __enter__(self):
        self._generate_k8s_config()
        self._load_config_file()
        if not self.pod_name:
            self._generate_model_path()
            self._generate_unique_name()

    def _generate_unique_name(self):
        if "." in self.version:
            version = self.version.replace(".", "-")
        else:
            version = self.version
        self.unique_name = (f"android{version}"
                            f"-{str(uuid.uuid1()).split('-')[0]}")

    def _generate_k8s_config(self, config_file=None):
        if not config_file:
            config_file = "config"
        if "dhub" in WORK_DIC:
            self.config = os.path.join(WORK_DIC, "configs", config_file)
        else:
            self.config = os.path.join(WORK_DIC, "dhub", "configs", config_file)

    def _generate_model_path(self):
        self.model_name = "emulator-cloud-template.yaml"
        if "dhub" in WORK_DIC:
            self.model_location = os.path.join(WORK_DIC, "configs",
                                               self.model_name)
        else:
            self.model_location = os.path.join(WORK_DIC, "dhub", "configs",
                                               self.model_name)

    def _load_config_file(self):
        config.load_kube_config(config_file=self.config)
        self.api_client = client.CoreV1Api()

    def create_pod(self):
        # Read the YAML file
        api_level = android_api_to_version[f'{self.version}']
        image = f"10.160.16.60/emulator-cloud/emulator_cloud:1.0.{api_level}"
        logger.info(f"going to use image {image}")

        logger.info(f"going to open files {self.model_location}")
        with open(self.model_location) as f:
            contents = f.read().split('---')
        logger.info(f"read the contents of model file")

        pod = yaml.safe_load(contents[0])
        pod["metadata"]["name"] = self.unique_name
        pod["metadata"]["labels"]["app"] = self.unique_name
        pod["spec"]["containers"][0]["image"] = image
        service = yaml.safe_load(contents[1])
        service["metadata"]["name"] = self.unique_name
        service["spec"]["selector"]["app"] = self.unique_name

        # Create the pod using the YAML manifest
        self.api_client.create_namespaced_pod(
            body=pod,
            namespace=NAMESPACE
        )

        self.api_client.create_namespaced_service(
            body=service,
            namespace=NAMESPACE
        )

        return self.unique_name

    def check_pod(self):
        try:
            resp = self.api_client.read_namespaced_pod_status(
                self.pod_name, NAMESPACE)
            status = resp.status.phase
        except client.ApiException as e:
            if e.status == 404:
                logger.info(f'Pod {self.pod_name} has been deleted already...')
                status = "deleted"
            else:
                status = "unknown"

        return status

    def check_android_status(self):
        try:
            exec_command = ['adb', 'shell', 'getprop', 'sys.boot_completed']
            resp = stream(
                self.api_client.connect_get_namespaced_pod_exec,
                self.pod_name,
                NAMESPACE,
                command=exec_command,
                # ADB command to check Android state
                stderr=True,  # Capture standard error
                stdin=False,  # No need for input
                stdout=True,  # Capture standard output
                tty=False  # No TTY required
            )
            # Check if Android has booted
            if resp.strip() == '1':
                print("Android has successfully booted.")
            else:
                print("Android is still booting.")
            return resp
        except Exception as e:
            print(f"Error while checking Android boot status: {e}")

    def enter_adb_command(self, text):
        try:
            if text.isdigit():
                exec_command = ['adb', 'shell', 'input', 'keyevent', text]
            else:
                exec_command = ['adb', 'shell', 'input', 'text', text]
            resp = stream(
                self.api_client.connect_get_namespaced_pod_exec,
                self.pod_name,
                NAMESPACE,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            # Check if Android has booted
            if resp.strip() == '':
                logger.info(f"adb command input text {text} done")
        except Exception as e:
            logger.info(f"adb command input text {text} done failed: {e}")

    def get_ports(self, unique_name: str = None):
        if unique_name:
            self.unique_name = unique_name
        res = self.api_client.read_namespaced_service(
            self.unique_name, NAMESPACE)
        for port in res.spec.ports:
            if port.port == VNC_PORT:
                self.vnc_node_port = port.node_port
            elif port.port == ABD_PORT:
                self.adb_node_port = port.node_port
        return self.vnc_node_port, self.adb_node_port

    def check_adb_port(self):
        try:
            # Try to establish a telnet connection
            with telnetlib.Telnet(
                    '10.160.24.88',
                    self.adb_node_port,
                    timeout=3):
                logger.info(f"the adb port {self.adb_node_port} is ready")
                return True
        except Exception:
            return False


    def delete_pod(self):
        try:
            self.api_client.delete_namespaced_pod(
                self.pod_name, namespace=NAMESPACE,
                body=client.V1DeleteOptions(propagation_policy='Foreground',
                                            grace_period_seconds=5))
        except client.ApiException as e:
            if e.status == 404:
                logger.info('Has been deleted already...')
                return "Deleted"
            else:
                logger.error(
                    'Delete pod "%s" failed, the detail error msg is :"%s"',
                    traceback.format_exc()
                )
                return "Failed"
        while True:
            try:
                resp = self.api_client.read_namespaced_pod_status(
                    self.pod_name, namespace=NAMESPACE
                )
                logger.info(f"pod {self.pod_name} current"
                            f" status is {resp.status.phase}")
            except client.ApiException as e:
                if e.status == 404:
                    logger.info(
                        f'Pod {self.pod_name} has been deleted successfully...'
                    )
                    self.api_client.delete_namespaced_service(
                        self.pod_name, namespace=NAMESPACE
                    )
                    while True:
                        try:
                            self.api_client.read_namespaced_service_status(
                                self.pod_name, namespace=NAMESPACE
                            )
                        except client.ApiException as e:
                            if e.status == 404:
                                logger.info(f'Service {self.pod_name}'
                                            f' has been deleted successfully...'
                                            )
                                return "Deleted"
                            else:
                                return "Failed"
                else:
                    logger.error(
                        'Delete pod %s failed, the detail error msg is :"%s"',
                        traceback.format_exc()
                    )
                    return "Failed"
            sleep(3)

    def list_all_pods(self):
        pods = []
        pod_list = self.api_client.list_namespaced_pod(namespace=NAMESPACE)
        for pod in pod_list.items:
            status = pod.status.phase
            name = pod.metadata.name
            version = name.split("-")[0]
            if status in ["Pending", "Running"]:
                ports = self.get_ports(name)
                pods.append({"name": name, "version": version,
                             "status": status, "vnc_port": ports[0],
                             "adb_port": ports[1]})
            else:
                pods.append({"name": name, "version:": version,
                             "status": status})
        return pods

