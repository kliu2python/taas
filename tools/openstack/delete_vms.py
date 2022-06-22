import openstack

SERVER_NAME_PREFIX = "fis-cluster"
STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)
EXCLUDE = ["fis-cluster-0", "fis-cluster-1", "fis-cluster-2"]

servers = conn.compute.servers(name="fis-cluster")
for server in servers:
    if server.name in EXCLUDE:
        print(f"skip deleting vm {server.name}")
        continue

    print(f"Deleting VM {server.name}")
    conn.compute.delete_server(server)
