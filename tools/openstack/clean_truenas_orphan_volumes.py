import urllib
import openstack
import requests


conn = openstack.connect("stack1")
host = "stack-1-store1@truenas-1#truenas-1"
api_key = "2-4hrKAUs2VQq7rducIraXD8vZT93DX8Uh1UzqcALTIvhDOriGZClvvliomIeo84Ca"
base_url = "http://10.160.83.8/api/v2.0"

volumes_not_delete = []
volumes_to_delete = []
exclude_project = ["service"]
pool_name = "storage"
dataset_name = "storage/cinder"


def get_current_volume_ids():
    global conn
    projects = conn.list_projects()
    for proj in projects:
        if proj.name in exclude_project:
            continue
        print(f"checking project: {proj.name}")
        conn = conn.connect_as_project(proj)
        for volume in conn.list_volumes():
            if host in volume.host:
                vol = volume.id.split("-")[0]
                print(f"Found using volumes: {vol}")
                volumes_not_delete.append(vol)


def request(method, api):
    url = base_url + api
    return requests.request(
        method, url, headers={
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {api_key}"
        }, verify=False
    )


def get_all_volumes():
    res = request("GET", "/iscsi/target")
    targets = {}
    if res.status_code == 200:
        for target in res.json():
            targets[target["name"]] = target["id"]
    else:
        raise Exception(f"Error when get volumes from truenas, {res.text}")

    textends = {}
    res = request("GET", "/iscsi/targetextent")
    for text in res.json():
        textends[text["target"]] = text["id"]

    res = request("GET", "/pool/dataset")
    if res.status_code == 200:
        for pool in res.json():
            if pool["id"] == pool_name:
                datasets = pool["children"]
                ds = list(
                    filter(lambda x: x["id"] == dataset_name, datasets)
                )[-1]
                if ds:
                    for volume in ds["children"]:
                        vol_id = volume["name"]
                        v_id = vol_id.split("-")[1]
                        if v_id in volumes_not_delete:
                            continue
                        volumes_to_delete.append(v_id)
                        print(f"volume to delete:  {v_id}")
                        res = request(
                            "DELETE",
                            f"/pool/dataset/id/"
                            f"{urllib.parse.quote_plus(vol_id)}"
                        )
                        if res.status_code == 200:
                            print(f"deleted zvol volume-{v_id}")
                        t_id = targets.get(f"target-{v_id}")
                        res = request("DELETE", f"/iscsi/target/id/{t_id}")
                        if res.status_code == 200:
                            print(f"deleted iscsi target target-{t_id}")
                else:
                    print(f"No data set {dataset_name} found")


get_current_volume_ids()
get_all_volumes()

