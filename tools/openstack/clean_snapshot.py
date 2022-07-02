import datetime
import os

import openstack


SNAP_SHOT_PREFIX = os.environ.get("SNAP_SHOT_PREFIX", "faccloud-,compl-")
STACK_NAME = os.environ.get("STACK_NAME", "stack1")
DAYS_KEEP = int(os.environ.get("DAYS_TO_KEEP", "30"))

conn = openstack.connect(STACK_NAME)
snapshot_prefix = SNAP_SHOT_PREFIX.split(",")
images = conn.image.images()

for image in images:
    if image.properties.get("image_type") in ["snapshot"]:
        for prefix in snapshot_prefix:
            if image.name.startswith(prefix):
                created_at = datetime.datetime.strptime(
                    image.created_at, "%Y-%m-%dT%H:%M:%SZ"
                )
                if (datetime.datetime.utcnow() - created_at).days > DAYS_KEEP:
                    print(f"Deleting image {image.name}")
                    conn.image.delete_image(image)
