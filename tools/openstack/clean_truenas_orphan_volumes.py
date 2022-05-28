import urllib
import openstack
import requests


conn = openstack.connect("stack1")
host = "stack-1-store1@truenas-1#truenas-1"
api_key = "xxxxxxxxx"
base_url = "http://10.160.83.8/api/v2.0"

volumes_not_delete = []
volumes_to_delete = []


def get_current_volume_ids():
    for volume in conn.list_volumes():
        if host in volume.host:
            volumes_not_delete.append(volume.id.split("-")[0])


def request(method, api):
    url = base_url + api
    return requests.request(
        method, url, headers={
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {api_key}"
        }
    )


def get_all_volumes():
    res = request("GET", "/iscsi/target")
    targets = {}
    for target in res.json():
        targets[target["name"]] = target["id"]

    textends = {}
    res = request("GET", "/iscsi/targetextent")
    for text in res.json():
        textends[text["target"]] = text["id"]

    res = request("GET", "/pool/dataset")
    if res.status_code == 200:
        volumes = res.json()[1]["children"]
        for volume in volumes:
            vol_id = volume["name"]
            v_id = vol_id.split("-")[1]
            if v_id in volumes_not_delete:
                continue
            volumes_to_delete.append(v_id)
            res = request(
                "DELETE", f"/pool/dataset/id/{urllib.parse.quote_plus(vol_id)}"
            )
            if res.status_code == 200:
                print(f"deleted zvol volume-{v_id}")
            t_id = targets.get(f"target-{v_id}")
            res = request("DELETE", f"/iscsi/target/id/{t_id}")
            if res.status_code == 200:
                print(f"deleted iscsi target target-{t_id}")


get_current_volume_ids()
print(volumes_not_delete)
get_all_volumes()

