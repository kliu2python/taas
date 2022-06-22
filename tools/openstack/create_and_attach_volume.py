import openstack


SERVER_NAME_BASE = "fis-cluster-254"
VOL_NAME_PREFIX = "data-vol"
VOL_SIZE = 30
CREATE_VOLUME = True
EXCLUDE_LIST = [f"{SERVER_NAME_BASE}-{i}" for i in range(1, 251)]

STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)

servers = conn.list_servers(filters={"name": SERVER_NAME_BASE})
for server in servers:
    print(f"*****Processing Server {server['name']}*****")
    if server["name"] in EXCLUDE_LIST:
        print("Skipping...")
        continue
    if CREATE_VOLUME:
        print(f"Creating volume...")
        vol = conn.create_volume(
            VOL_SIZE, name=f"{VOL_NAME_PREFIX}-{server['name']}"
        )
    else:
        vol = conn.get_volume(f"{VOL_NAME_PREFIX}-{server['name']}")

    print("Attaching volume...")
    conn.attach_volume(server, vol)
    print("Done")
    conn.compute.reboot_server(server["id"], "HARD")
    print("Hard reboot...")
