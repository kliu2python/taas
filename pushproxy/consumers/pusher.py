import json

from pushproxy.common.conf import CONF
from pushproxy.common.pushproxy import PushGateway
from pushproxy.tasks.lifecycle import register_alive
from utils.logger import get_logger


LOGGER = get_logger()
PUSH_GATEWAY = CONF.get("push_gateway")


def upload_to_push_proxy(data, job, time=None, grouping_key=None):
    """
    counter value with labels:
    [
        {
            labels: {
                label_name1: label1,
                label_name2: label2
            }
            value: xxx
        }
    ]
    """
    try:
        push_proxy = PushGateway.get_pushproxy(job)
        if not push_proxy:
            push_proxy = PushGateway(
                PUSH_GATEWAY, job, grouping_key=grouping_key
            )
        push_proxy.push(data, time)
    except Exception as e:
        LOGGER.exception("", exc_info=e)


def consume_data(message):
    data = json.loads(message)
    push_job_name = data.get("job")

    time = data.pop("time")
    res = data.get("data")
    timeout = data.get("timeout")

    upload_to_push_proxy(res, push_job_name, time)

    register_alive(push_job_name, timeout)
