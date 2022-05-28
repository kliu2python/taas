import openstack


VOL_SIZE = 30
COUNT = 30

STACK_NAME = "stack1"

conn = openstack.connect(STACK_NAME)

for _ in range(COUNT):
    conn.create_volume(VOL_SIZE)