import openstack


CLOUD_NAME = "stack1"
NETWORK_NAME = "faccloud"

conn = openstack.connect(CLOUD_NAME)
network = conn.get_network(NETWORK_NAME)

ports = conn.network.ports(network_id=network.id, status="DOWN")
for port in ports:
    if "faccloud-" in port.name:
        print(f"deleting port {port.name}")
        conn.network.delete_port(port)
