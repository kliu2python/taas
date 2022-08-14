from fos.conf import CONF
from fos.dispatcher import RqDispatcher
from fos.infostie import InfoSiteClient

from utils.logger import get_logger

dispatcher = RqDispatcher(CONF.get("job", {}).get("timeout", 30))
logger = get_logger()


def get_fos_platforms(**target):
    with InfoSiteClient() as client:
        client.download(**target)


def register_jobs():
    for target in CONF["targets"]:
        logger.info(f"registering job: {target}")
        dispatcher(get_fos_platforms, job_args=target)

    dispatcher.start()
