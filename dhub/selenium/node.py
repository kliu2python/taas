import os
import json
import requests
import traceback
from time import sleep

import yaml
from kubernetes import (
    client,
    config
)
from kubernetes import stream

from utils.logger import get_logger

URL = "http://10.160.24.88:31590/status"
logger = get_logger()
WORK_DIC = os.getcwd()
NAMESPACE = "selenium-grid"


class Node:
    def __init__(self,  node_name: str, browser: str = None,
                 version: str = None, portal_ip: list = None):
        self.availability = "Down"
        self.browser = browser
        self.node_name = node_name
        self.version = version
        self.portal_ip = portal_ip
        self.session_id = None
        self.pod_config = None
        self.model_location = None
        self.__enter__()

    def __enter__(self):
        self._generate_k8s_config()
        self._load_config_file()
        self._generate_model_path()

    def _generate_k8s_config(self):
        if "dhub" not in WORK_DIC:
            self.config = os.path.join(WORK_DIC, "dhub", "configs", "config")
        else:
            self.config = os.path.join(WORK_DIC, "configs", "config")

    def _generate_model_path(self):
        if "dhub" not in WORK_DIC:
            self.model_location = os.path.join(WORK_DIC, "dhub", "configs",
                                               "browser-cloud-template.yaml")
        else:
            self.model_location = os.path.join(WORK_DIC, "configs",
                                               "browser-cloud-template.yaml")

    def _load_config_file(self):
        config.load_kube_config(config_file=self.config)
        self.api_client = client.CoreV1Api()

    def create_pod(self):
        res = self.check_pod()
        if res in ["Running", "Pending"]:
            return f"{self.node_name} exists already"
        elif res in ["Completed"]:
            self.delete_pod()
            logger.info(f"Deleted Completed pod {self.node_name}, recreate..")

        with open(self.model_location) as f:
            contents = f.read().split('---')

        if self.browser in ['chrome', 'googlechrome']:
            browser_name = 'chrome'
            image_name = 'chrome'
            options = "goog:chromeOptions"
            driver_path = "/usr/bin/google-chrome"
        elif self.browser == 'firefox':
            browser_name = 'firefox'
            image_name = 'firefox'
            options = "moz:firefoxOptions"
            driver_path = "/usr/bin/firefox"
        elif self.browser == 'edge':
            browser_name = 'MicrosoftEdge'
            image_name = 'edge'
            options = "ms:edgeOptions"
            driver_path = "/usr/bin/microsoft-edge"
        else:
            raise NameError(f"{self.browser} is not correct input")

        # Read the YAML file
        image = f"selenium/node-{image_name}:{self.version}"
        logger.info(f"going to use image {image}")

        pod = yaml.safe_load(contents[0])
        pod["metadata"]["name"] = self.node_name
        pod["spec"]["containers"][0]["image"] = image
        if self.portal_ip:
            if len(self.portal_ip) > 0:
                pod["spec"]["hostAliases"] = []
                for portal_ip in self.portal_ip:
                    for ip, hostname in portal_ip.items():
                        host_alias_entry = {
                            "ip": ip,
                            "hostnames": [hostname]
                        }
                        pod["spec"]["hostAliases"].append(host_alias_entry)
        new_stereotype = (
            "{\"browserName\":\"newBrowserName\","
            "\"browserVersion\":\"newBrowserVersion\","
            "\"nodename:applicationName\":\"newNodeName\","
            "\"platformName\": \"Linux\","
            "\"newOptions\": {\"binary\": \"newPath\"}}"
        )
        new_stereotype = new_stereotype.replace(
            "newBrowserName", browser_name
        ).replace(
            "newBrowserVersion", self.version
        ).replace(
            "newNodeName", self.node_name
        ).replace(
            "newOptions", options
        ).replace(
            "newPath", driver_path
        )
        pod["spec"]["containers"][0]["env"][5]["value"] = new_stereotype

        # Create the pod using the YAML manifest
        self.api_client.create_namespaced_pod(
            body=pod,
            namespace=NAMESPACE
        )

        return self.node_name

    def check_pod(self):
        try:
            resp = self.api_client.read_namespaced_pod_status(
                self.node_name, NAMESPACE
            )
            status = resp.status.phase
        except client.ApiException as e:
            if e.status == 404:
                logger.info(f'Pod {self.node_name} has been deleted already')
                status = "deleted"
            else:
                status = "unknown"

        return status

    def delete_pod(self):
        try:
            self.api_client.delete_namespaced_pod(
                self.node_name, namespace=NAMESPACE,
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
                    self.node_name, namespace=NAMESPACE
                )
                logger.info(f"pod {self.node_name} current"
                            f" status is {resp.status.phase}")
            except client.ApiException as e:
                if e.status == 404:
                    logger.info(
                        f'Pod {self.node_name} has been deleted successfully.'
                    )
                    break
                else:
                    logger.error(
                        'Delete pod %s failed, the detail error msg is :"%s"',
                        traceback.format_exc()
                    )
                    return "Failed"
            sleep(3)
        return "Deleted"

    def check_selenium_node_status(self):
        try:
            response = requests.get(URL)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print(f"Http Error: {errh}")
            return None
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
            return None
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"OOps: Something Else: {err}")
            return None

        status_data = response.json()
        nodes = status_data['value']['nodes']
        for node in nodes:
            for slots in node.get('slots', []):
                if 'nodename:applicationName' in slots['stereotype']:
                    name = slots['stereotype']['nodename:applicationName']
                    if name != self.node_name:
                        break
                    self.availability = node.get('availability')
                    return self.availability
        return self.availability

    def check_selenium_hostname_point(self, commands: str):
        exec_command = []
        count = 3
        while count > 0:
            try:
                command_list = commands.split(" ")
                for command in command_list:
                    exec_command.append(command)
                resp = stream.stream(
                    self.api_client.connect_get_namespaced_pod_exec,
                    self.node_name, NAMESPACE, command=exec_command, stderr=True,
                    stdin=False, stdout=True, tty=False)
                if 'Connected' in resp:
                    if "https://ftc.fortinet.com/version" in exec_command:
                        resp = resp.split("\n")[-2]
                        resp = json.loads(resp)
                    logger.info(f"Response: {resp}")
                    return resp
                count -= 1
            except client.exceptions.ApiException as e:
                logger.info(f"Exception when calling {e}")

