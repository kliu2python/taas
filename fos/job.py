from fos.conf import CONF
from fos.dispatcher import RqDispatcher
from fos.infostie import InfoSiteClient
from fos.platforms import Fortigate

from utils.logger import get_logger

dispatcher = RqDispatcher()
logger = get_logger()


def get_fos_platforms(**target):
    with InfoSiteClient() as client:
        client.set_build(**target)
        data = client.download("platform.xml")

    Fortigate(data.decode()).update()


def register_jobs():
    for target in CONF["targets"]:
        logger.info(f"registering job: {target}")
        dispatcher(get_fos_platforms, job_args=target)

    dispatcher.start()
