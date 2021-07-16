import uuid
from typing import List, Dict, Union

import eventlet
from singleton_decorator.decorator import singleton

from utils.logger import get_logger

eventlet.monkey_patch()
logger = get_logger()


# noinspection PyBroadException
@singleton
class ThreadsManager:
    def __init__(self):
        """
        processes dict:
        {
            caller_id: processes
        }
        """
        self._data: Dict[str, object] = {}
        self._status: Dict[str, Union[str, Exception]] = {}
        self._threads: Dict[str, eventlet.greenthread.GreenThread] = {}

    def _func_wrapper(self, *args_func, **kwargs_func):
        caller_id = args_func[0]
        func = args_func[1]
        args_func = tuple(list(args_func)[2:])
        try:
            result = func(*args_func, **kwargs_func)
            self._status[caller_id] = "SUCCESS"
            self._data[caller_id] = result
        except Exception as ex:
            self._status[caller_id] = ex

    def start_thread(self, caller_id, target, *args, **kwargs):
        args = (caller_id, target) + args

        task = eventlet.spawn(self._func_wrapper, *args, **kwargs)
        self._threads[caller_id] = task
        logger.info(f"started process for {caller_id}")

    def _remove_completed_threads(self, caller_id):
        threads = self._threads.get(caller_id)
        if threads is not None:
            self._threads.pop(caller_id)

    def wait_for_complete(
            self,
            caller_ids: List[str],
            kill_immediately=False,
            timeout=300
    ) -> Union[None, object]:
        logger.info(f"waiting for process {caller_ids} complete")
        for cid in caller_ids:
            task = self._threads.pop(cid, None)
            if task is not None:
                if kill_immediately:
                    try:
                        logger.info(f"Killing {cid}")
                        task.kill()
                    except Exception as e:
                        logger.exception(
                            f"Error when kill thread {cid}", exc_info=e
                        )
                else:
                    killed = False
                    try:
                        if timeout > 0:
                            with eventlet.Timeout(timeout):
                                task.wait()
                        else:
                            task.wait()
                    except eventlet.Timeout:
                        logger.warning(
                            f"Thread {cid} fail to stop in 60 seconds, killing")
                        task.kill()
                        killed = True
                    if not killed:
                        status = self._status.get(cid)
                        if status not in ["SUCCESS"]:
                            logger.exception(
                                f"Thread {cid} running Error", exc_info=status
                            )
            else:
                logger.error(f"Thread {cid} Not Found!")
            self._status.pop(cid, None)
        return [self._data.pop(cid, None) for cid in caller_ids]


def thread_run(func, *args, **kwargs):
    """
    if you do not want to use decorator, you can also use this static function.
    """
    caller_id = uuid.uuid4()
    ThreadsManager().start_thread(
        caller_id, func, *args, **kwargs
    )
    return caller_id


def thread(func):
    """
    a decorator to make function run in parallel. the function will return
    caller id in UUID object.
    """
    def warp_arg(*args, **kwargs):
        return thread_run(func, *args, **kwargs)
    return warp_arg


thread_manager = ThreadsManager()
