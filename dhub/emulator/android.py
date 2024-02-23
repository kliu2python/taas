import os
import uuid
import yaml

from kubernetes import (
    client,
    config
)

from dhub.resources.api_level_comparison_table import android_api_to_version

WORK_DIC = os.getcwd()
NAMESPACE = "emulator-cloud"
VNC_PORT = 6901
ABD_PORT = 4723


class AndroidEmulator:
    def __init__(self, version, dns):
        self.config = None
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
        self._generate_model_path()
        self._generate_unique_name()

    def _generate_unique_name(self):
        self.unique_name = f"android{self.version}-{str(uuid.uuid1()).split('-')[0]}"

    def _generate_k8s_config(self, config_file=None):
        if not config_file:
            config_file = "config"
        self.config = os.path.join(WORK_DIC, "dhub", "configs", config_file)

    def _generate_model_path(self):
        base_name = "emulator-cloud-api"
        self.model_name = f"{base_name}{android_api_to_version[f'{self.version}']}.yaml"
        self.model_location = os.path.join(WORK_DIC, "dhub", "configs", self.model_name)

    def _load_config_file(self):
        config.load_kube_config(config_file=self.config)
        self.api_client = client.CoreV1Api()

    def create_pod(self):
        # Read the YAML file
        with open(self.model_location) as f:
            contents = f.read().split('---')

        pod = yaml.safe_load(contents[0])
        pod["metadata"]["name"] = self.unique_name
        pod["metadata"]["labels"]["app"] = self.unique_name
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

    def get_ports(self, unique_name: str = None):
        if unique_name:
            self.unique_name = unique_name
        res = self.api_client.read_namespaced_service(self.unique_name, NAMESPACE)
        for port in res.spec.ports:
            if port.port == VNC_PORT:
                self.vnc_node_port = port.node_port
            elif port.port == ABD_PORT:
                self.adb_node_port = port.node_port
        return self.vnc_node_port, self.adb_node_port
