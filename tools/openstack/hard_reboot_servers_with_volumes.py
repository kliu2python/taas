import openstack

conn = openstack.connect("stack1")
host = "stack-1-store1@truenas-1#truenas-1"

for volume in conn.list_volumes():
    if "error" in volume.get("status"):
        continue

    if host in volume.host:
        if volume.attachments:
            servers = conn.search_servers(volume.attachments[0].server_id)
            for server in servers:
                print(f"Rebooting Server {server.name}")
                conn.compute.reboot_server(server.id, "HARD")
