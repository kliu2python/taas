import threading
from queue import Queue

import openstack

ACTION = "resize"
SERVER_NAME_PREFIX = "fis-cluster"
FLAVOR = "fis.medium"
STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)

servers = conn.compute.servers(name=SERVER_NAME_PREFIX)
flavor = conn.get_flavor(FLAVOR)

servers_waiting = Queue()
event = threading.Event()


def confirm_server():
    while True:
        s = servers_waiting.get()
        if s.status.lower() == "verify_resize":
            print(f"Confirming server {s.name}")
            conn.compute.confirm_server_resize(s)
        elif s.status.lower() == "error":
            print(f"Error when resizing {s.name}")
            print(f"resetting server {server.name}")
            conn.compute.reset_server_state(s, "active")
            conn.compute.reboot_server(s, "HARD")
        else:
            servers_waiting.put(s)
            continue
        event.set()


if ACTION == "resize":
    threading.Thread(target=confirm_server).start()
    for server in servers:
        if server.flavor.original_name == FLAVOR:
            print(f"Server {server.name} already be {FLAVOR}")
            continue

        print(f"Resizing Server {server.name}")
        conn.compute.resize_server(server, flavor["id"])
        servers_waiting.put(server)

        if servers_waiting.qsize() >= 1:
            event.clear()
            event.wait()
