import os

import openstack
import yaml


SERVER_NAME_BASE = "fis-cluster2"
VOL_NAME_PREFIX = "fis-data2"
IMAGE = "fis-0488"
FLAVOR = "fis.medium"
NETWORKS = [
    "fis-internal",
    "fis-external",
    "fis-mgmt",
    "fis-ha"
]

RANGE = [0, 255]
KEYNAME = ""
SYS_VOL_SIZE = 10
DATA_VOL_SIZE = 30
STACK_NAME = "stack1"
EXCLUDE_IP = ["10.2.3.99", "10.2.3.96", "10.2.3.86"]

conn = openstack.connect(STACK_NAME)

with open("register_code_mapping.yaml") as F:
    ip_pools = list(yaml.safe_load(F)["assigned"].keys())

if os.path.exists("created.yaml"):
    with open("created.yaml") as F:
        created = yaml.safe_load(F)
else:
    created = {}

ip_pools = list(set(ip_pools) - set(created.values()) - set(EXCLUDE_IP))


def create_servers():
    image = conn.compute.find_image(IMAGE)
    flavor = conn.compute.find_flavor(FLAVOR)
    networks = []
    for network in NETWORKS:
        network = conn.network.find_network(network)
        networks.append({"uuid": network.id})

    kwargs = {}
    if KEYNAME:
        kwargs["key_name"] = KEYNAME

    if SYS_VOL_SIZE:
        kwargs["block_device_mapping_v2"] = []
        block_mapping = {
            'boot_index': '0',
            'delete_on_termination': True,
            'destination_type': 'volume',
            'uuid': image.id,
            'source_type': 'image',
            'volume_size': SYS_VOL_SIZE,
        }
        kwargs['block_device_mapping_v2'].append(block_mapping)

    for i in range(*RANGE):
        name = f"{SERVER_NAME_BASE}-{i}"
        if name in created:
            print(f"server: {name} already created, skipping")
            continue
        mgmt_ip = ip_pools.pop()
        networks[2]["fixed_ip"] = mgmt_ip
        created[name] = mgmt_ip
        server = conn.compute.create_server(
            name=name,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=networks,
            **kwargs
        )
        server = conn.compute.wait_for_server(server)
        print(f"created server {server.name}")
        print(f"Creating volume...")
        vol = conn.create_volume(
            DATA_VOL_SIZE, name=f"{VOL_NAME_PREFIX}-{server['name']}"
        )
        server = conn.get_server(server.name)
        conn.attach_volume(server, vol)
        with open("created.yaml", "w") as FILE:
            yaml.safe_dump(created, FILE)


def get_ips():
    servers = []
    for i in range(*RANGE):
        name = f"{SERVER_NAME_BASE}{i}"
        server = conn.get_server(name_or_id=name)
        ip = getattr(server.addresses, NETWORKS[0])[0]["addr"]
        servers.append(ip)

    for server in servers:
        print(server)

    print("\n======\n")

    for server in servers:
        print(" " * 15 + f"- {server}:9100")


create_servers()
# get_ips()
