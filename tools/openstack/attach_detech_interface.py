import time

import openstack


CLOUD_NAME = "stack1"

TARGET_IP_BEGIN = "192.168"
ATTACH_INTERFACE_FROM = "fis-ha"
SERVER_NAME = "fis-cluster"

conn = openstack.connect(CLOUD_NAME)

servers = conn.list_servers(filters={"name": SERVER_NAME})
for server in servers:
    server = conn.compute.get_server(server["id"])

    interfaces = conn.compute.server_interfaces(server)
    stop = False
    for interface in interfaces:
        if interface.fixed_ips[0]["ip_address"].startswith(TARGET_IP_BEGIN):
            stop = True
            # conn.compute.delete_server_interface(interface)
            # print(f"deleted interface for server {server.name}")
    if stop:
        print(f"skipping for server {server.name}")
        continue
    if ATTACH_INTERFACE_FROM:
        net = conn.get_network(ATTACH_INTERFACE_FROM)
        print(f"Attaching interface {net['id']} for server {server.name}")
        conn.compute.create_server_interface(server, net_id=net["id"])
    time.sleep(1)
