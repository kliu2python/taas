import openstack


SERVER_NAME_BASE = "taas-runner-"
IMAGE = "ubuntu20.04-k8s"
FLAVOR = "m1.xlarge.hdd"
NETWORK = "internal-automation"
RANGE = [1, 7]

STACK_NAME = "stack1"

conn = openstack.connect(STACK_NAME)


def create_servers():
    for i in range(*RANGE):
        name = f"{SERVER_NAME_BASE}{i}"
        server = conn.create_server(
            name=name,
            image=IMAGE,
            flavor=FLAVOR,
            terminate_volume=True,
            network=NETWORK,
            boot_from_volume=True,
            volume_size=100,
            key_name="cloudqa"
        )
        print(getattr(server.addresses, NETWORK)[0]["addr"])


def get_ips():
    servers = []
    for i in range(*RANGE):
        name = f"{SERVER_NAME_BASE}{i}"
        server = conn.get_server(name_or_id=name)
        ip = getattr(server.addresses, NETWORK)[0]["addr"]
        servers.append(ip)

    for server in servers:
        print(server)

    print("\n======\n")

    for server in servers:
        print(" " * 15 + f"- {server}:9100")


# create_servers()
get_ips()
