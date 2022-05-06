import os

import yaml
import openstack
import requests


CLOUD_NAME = "stack1"

conn = openstack.connect(CLOUD_NAME)
project_id = conn.current_project.get("id")

_OS_AUTH_URL = "http://10.160.83.5:5000/v3/auth/tokens?nocatalog"
_OS_VOL_URL = "http://10.160.83.5:8776/v3"
config_path = os.path.join(os.path.dirname(__file__), "clouds.yml")

with open(config_path) as F:
    auth = yaml.safe_load(F).get("clouds", {}).get(CLOUD_NAME, {}).get("auth")

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
    _OS_AUTH_URL, json=auth_dict, headers={"Content-Type": "application/json"}
)

token = None

if resp.status_code == 201:
    token = resp.headers.get("X-Subject-Token")

if not token:
    raise Exception(
        f"Error when get token, resp={resp.status_code}, {resp.text}"
    )


def _delete_volume_attachement(att_id):
    res = requests.delete(
        f"{_OS_VOL_URL}/{project_id}/attachments/{att_id}",
        headers={"X-Auth-Token": token, "OpenStack-API-Version": "volume 3.27"}
    )
    if res.status_code == 200:
        print(f"delete attachment success for {att_id}")
        return True
    else:
        print(
            f"delete attachment failed for {att_id}, "
            f"{res.status_code}, {res.text}"
        )
        return False


volumes = conn.volume.volumes()
for vol in volumes:
    if vol.status == "in-use":
        for att in vol.attachments:
            server_id = att.get("server_id")
            if server_id:
                server = conn.get_server(server_id)
                if not server:
                    ret = _delete_volume_attachement(att.get("attachment_id"))
                    if ret:
                        print(f"Deleting volume: {vol.id}")
                        conn.delete_volume(vol.id)
