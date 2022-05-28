import os

import yaml
import openstack
import requests

_OS_AUTH_URL = "http://10.160.83.5:5000/v3/auth/tokens?nocatalog"
config_path = os.path.join(os.path.dirname(__file__), "clouds.yml")


class OpenstackApiClient:
    def __init__(self, cloud_name):
        self.cloud_name = cloud_name
        conn = openstack.connect(self.cloud_name)
        self.project_id = conn.current_project.get("id")

        with open(config_path) as F:
            auth = yaml.safe_load(F)["clouds"][self.cloud_name]["auth"]

        auth_dict = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "domain": {"name": f"{auth['user_domain_name']}"},
                            "name": f"{auth['username']}",
                            "password": f"{auth['password']}"
                        }
                    }
                },
                "scope": {
                    "project": {
                        "domain": {
                            "name": f"{auth['project_domain_name']}"
                        },
                        "name":  f"{auth['project_name']}"
                    }
                }
            }
        }

        resp = requests.post(
            _OS_AUTH_URL,
            json=auth_dict,
            headers={"Content-Type": "application/json"}
        )

        self.token = None

        if resp.status_code == 201:
            self.token = resp.headers.get("X-Subject-Token")

        if not self.token:
            raise Exception(
                f"Error when get token, resp={resp.status_code}, {resp.text}"
            )

    def request(self, method, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers.update({"X-Auth-Token": self.token})
        res = requests.request(
            method,
            url,
            headers=headers,
            **kwargs
        )
        return res
