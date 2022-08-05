import os
from time import sleep

from redis import Redis
from rq import Queue
from rq import Retry

from fos.conf import CONF
from utils.logger import get_logger

LOGGER = get_logger()
DEBUG = os.environ.get("DEBUG", "False") != "True"


def init_rq():
    conn = Redis(
        host=CONF["redis"]["server"],
        port=CONF.get("redis", {}).get("redis_port", 6379),
        decode_responses=True
    )
    # to debug , set is_async to False
    return Queue(connection=conn, default_timeout=30, is_async=DEBUG)


class RqDispatcher:
    jobs = []

    def __init__(self, interval=30):
        self.queue = init_rq()
        self._interval = interval
        self._running = True

    def __call__(self, job, **kwargs):
        """
        class function  for register jobs to dispatch

        job : func
        job_args=None,
        interval=30,
        stop_callback=None,
        callback_args=None
        stop_callback: method.
        callback_args: dict
        """
        if kwargs is None:
            kwargs = {}
        self.jobs.append([job, kwargs])

    def _dispatch_all_jobs(self):
        for job in self.jobs:
            try:
                kwargs = job[1]
                stop_callback = kwargs.get("stop_callback")
                if stop_callback:
                    callback_args = kwargs.get("callback_args")
                    callback_result = (
                        stop_callback(**callback_args)
                        if callback_args else stop_callback()
                    )
                    if callback_result:
                        break
                self.queue.enqueue(
                    job[0], **kwargs.get("job_args", {}), retry=Retry(max=3)
                )
            except Exception as e:
                LOGGER.exception("Error for execute job", exc_info=e)

    def start(self):
        while self._running:
            self._dispatch_all_jobs()
            sleep(self._interval)
