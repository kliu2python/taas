import datetime
from time import sleep

from utils.logger import get_logger
from utils.threads import thread, ThreadsManager

logger = get_logger()


class TestUtilsThreads:
    running = False

    @thread
    def _check_curr_time(self, target):
        current_time = datetime.datetime.now()
        logger.info(f"targets = {target}")
        logger.info(f"Curr Time = {current_time}")
        while self.running:
            current_time = datetime.datetime.now()
            sleep(3)
        return target, current_time

    def test_threads_wait_exit(self):
        target = ["Test1", "Test2", "Test3"]
        self.running = True
        cid = self._check_curr_time(target)
        sleep(5)
        self.running = False
        ret = ThreadsManager().wait_for_complete([cid], kill_immediately=False)
        assert ret[0][0] == target
        assert (datetime.datetime.now() - ret[0][1]).seconds < 5

    def test_threads_kill(self):
        target = ["Test1", "Test2", "Test3"]
        self.running = True
        cid = self._check_curr_time(target)
        sleep(5)
        self.running = False
        ret = ThreadsManager().wait_for_complete([cid], kill_immediately=True)
        assert ret == [None]
