from time import sleep

import openstack


EXCLUDE = ["fis-cluster-0", "fis-cluster-1", "fis-cluster-2"]
conn = openstack.connect("stack1")
START = False

filters = {
    "name": "fis-cluster"
}

i = 0
for server in conn.compute.servers(**filters):
    if server.name in EXCLUDE or server.vm_state in ["stopped"]:
        print(f"skipping {server.name}")
        continue
    print(f"Stopping server {server.name}")
    if START:
        conn.compute.start_server(server)
    else:
        conn.compute.stop_server(server)
    i += 1
    if i > 10:
        sleep(20)
        i = 0
