import openstack

conn = openstack.connect("stack1")

filters = {
    "OS-EXT-SRV-ATTR:host": "xxxxx"
}

for server in conn.search_servers(filters=filters):
    print(f"hard reboot for server {server.name}")
    conn.compute.reboot_server(server.id, "HARD")
