from time import sleep

import openstack

conn = openstack.connect("stack1")

filters = {
    "name": "fis-cluster"
}

i = 0
for server in conn.list_servers(filters=filters):
    print(f"hard reboot for server {server.name}")
    conn.compute.reboot_server(server.id, "HARD")
    i += 1
    if i > 10:
        sleep(20)
        i = 0
