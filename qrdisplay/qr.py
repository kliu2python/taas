import base64
import datetime
import json
import os
import uuid
from io import BytesIO

from PIL import Image
from utils.logger import get_logger

from .constants import LOCK_FILE
from .driver.display import Display

logger = get_logger()


def get_display():
    if not os.path.exists(LOCK_FILE):
        session_id = str(uuid.uuid4())
        session_data = {
            "results": "OK",
            "reserve_id": session_id,
            "time": datetime.datetime.now().timestamp()
        }
        with open(LOCK_FILE, "w") as FILE:
            json.dump(session_data, FILE)
        return session_data


def release_display(reserve_id):
    if verify_client(reserve_id):
        os.remove(LOCK_FILE)
        Display().reset()
        return "SUCCESS"
    return "Not Authorized"


def verify_client(reserve_id):
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as FILE:
            session_data = json.load(FILE)
        if session_data.get("reserve_id") == reserve_id:
            return True
    return False


def show_qrcode(reserve_id, image):
    display = Display()
    try:
        if verify_client(reserve_id):
            img_bytes = base64.b64decode(image)
            img_stream = BytesIO(img_bytes)
            img = Image.open(img_stream)
            img = img.convert("RGB").resize((240, 240))
            display.init()
            display.clear()
            display.show_img(img)
            return "SUCCESS"
        return "Not Authorized"
    except Exception as e:
        logger.exception("Error when show qr code", exc_info=e)
        display.reset()
        return "FAIL"
