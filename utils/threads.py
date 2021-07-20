import threading
import uuid
from typing import List, Dict, Union

from singleton_decorator.decorator import singleton

from utils.logger import get_logger

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
        self._threads: Dict[str, threading.Thread] = {}

    def _func_wrapper(self, *args_func, **kwargs_func):
        caller_id = args_func[0]
        func = args_func[1]
        args_func = tuple(list(args_func)[2:])
        try:
            result = func(*args_func, **kwargs_func)
            self._status[caller_id] = "SUCCESS"
            self._data[caller_id] = result
        except Exception as e:
            logger.exception("Error when start run", exc_info=e)

    def start_thread(self, caller_id, target, *args, **kwargs):
        args = (caller_id, target) + args

        task = threading.Thread(
            target=self._func_wrapper, args=args, kwargs=kwargs, daemon=True
        )
        task.start()
        self._threads[caller_id] = task
        logger.info(f"started process for {caller_id}")

    def _remove_completed_threads(self, caller_id):
        threads = self._threads.get(caller_id)
        if threads is not None:
            if not threads.is_alive():
                self._threads.pop(caller_id)

    def wait_for_complete(
            self, caller_ids: List[str], ignore_error=False
    ) -> Union[None, object]:

        logger.info(f"waiting for all process under {caller_ids} complete")

        for cid in caller_ids:
            task = self._threads.get(cid)
            if task is not None and task.is_alive():
                try:
                    task.join()
                except Exception:
                    pass
            status = self._status.get(cid)
            if status not in ["SUCCESS"] and not ignore_error:
                if isinstance(status, Exception):
                    raise status
                raise RuntimeError("Thread running error!")
            self._remove_completed_threads(cid)
        return [self._data.get(cid) for cid in caller_ids]


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
