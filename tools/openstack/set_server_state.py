import openstack

conn = openstack.connect("stack1")

filters = {
    "OS-EXT-SRV-ATTR:host": "stack-1-compute17-nvm",
    "OS-EXT-STS:vm_state": "error"
}

for server in conn.search_servers(filters=filters):
    print(f"reset state to active for server {server.name}")
    conn.compute.reset_server_state(server.id, "active")
