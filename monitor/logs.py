import datetime
import uuid

import monitor.constants as constants
import monitor.models as db
from utils.logger import get_logger

logger = get_logger()


def add_log(data):
    logs = data.pop("logs")
    if logs:
        session_id = str(uuid.uuid4())
        data["id"] = session_id
        data["create_at"] = datetime.datetime.now()
        data["repeats"] = len(logs)
        db.LogEntry.add_once(data)
        service_ip = getattr(constants.SYS_CONFIG, "service_ip", "10.160.13.10")
        for log in logs:
            png_b64 = log.pop("screencap")
            img_id = None
            if png_b64:
                img_id = str(uuid.uuid4())
                db.Image.add_once(
                    {
                        "id": img_id,
                        "img_data": png_b64,
                        "img_url": constants.IMG_URL_TEMPLATE.format(
                            ip=service_ip,
                            id=img_id
                        )
                    }
                )
            log["id"] = str(uuid.uuid4())
            log["attachment_id"] = img_id
            log["session_id"] = session_id
            db.Message.add_once(log)


def get_screen_cap(img_id):
    img = db.Image.query_once(query_filter=db.Image.id.like(img_id)).all()
    if img:
        return img[-1].img_data
    logger.info(f"No image found for id: {img_id}")
