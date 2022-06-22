import openstack

STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)

volumes = conn.list_volumes()

for vol in volumes:
    if vol.get("status") in ["available"]:
        print(f"deleting {vol.get('name')}")
        conn.delete_volume(vol.get("id"))
    else:
        print(f"skipping {vol.get('name')}")
