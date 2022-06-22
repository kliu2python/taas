import openstack

conn = openstack.connect("stack2")
host = "stack-1-store1"

for volume in conn.block_storage.volumes():
    if "error" in volume.status:
        continue

    # if host in volume.host:
    if volume.attachments:
        servers = conn.search_servers(volume.attachments[0]["server_id"])
        for server in servers:
            print(f"Rebooting Server {server.name}")
            conn.compute.reboot_server(server.id, "HARD")
