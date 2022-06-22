import openstack

# SERVER_NAME_PREFIX = "fis-cluster"
STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)

servers = conn.compute.servers(status="error")
for server in servers:
    print(f"resetting server {server.name}")
    conn.compute.reset_server_state(server, "active")
    conn.compute.reboot_server(server, "HARD")
