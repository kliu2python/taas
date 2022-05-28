import openstack


SERVER_NAME_BASE = "fis-cluster"
IMAGE = "fis-0464"
FLAVOR = "fis.small"
NETWORKS = [
    "fis-internal",
    "fis-external",
    "fis-mgmt",
    "fis-ha"
]
RANGE = [1, 2]
KEYNAME = ""
VOL_SIZE = 30

STACK_NAME = "stack1"

conn = openstack.connect(STACK_NAME)


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

    if VOL_SIZE:
        kwargs["block_device_mapping_v2"] = []
        block_mapping = {
            'boot_index': '0',
            'delete_on_termination': True,
            'destination_type': 'volume',
            'uuid': image.id,
            'source_type': 'image',
            'volume_size': VOL_SIZE,
        }
        kwargs['block_device_mapping_v2'].append(block_mapping)

    for i in range(*RANGE):
        name = f"{SERVER_NAME_BASE}-{i}"
        server = conn.compute.create_server(
            name=name,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=networks,
            **kwargs
        )
        server = conn.compute.wait_for_server(server)
        print(f"created server {server.name}")


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
