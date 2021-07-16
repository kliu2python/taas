import datetime
import json
import os
import time

import utils.rest as rest
from utils.logger import get_logger
from qrdisplay.constants import LOCK_FILE

TIMEOUT_SECONDS = 2 * 60
logger = get_logger()

while True:
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as FILE:
            data = json.load(FILE)
        display_time = data.get("time")
        reserve_id = data.get("reserve_id")
        payload = {"reserve_id": reserve_id}
        if datetime.datetime.now().timestamp() - display_time > TIMEOUT_SECONDS:
            logger.info(f"Cleaning display: {data}")
            rest.rest_call(
                "localhost",
                "/qrdisplay/display",
                method="DELETE",
                json=payload
            )

    time.sleep(30)
