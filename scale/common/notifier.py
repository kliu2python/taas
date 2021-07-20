# pylint: disable=too-many-arguments,too-many-instance-attributes,
# pylint: disable=unused-argument
from time import sleep

from utils.logger import get_logger
from utils.threads import thread, ThreadsManager
from scale.common.constants import RunnerStatus

logger = get_logger()


class Notifier:
    def __init__(
            self,
            session,
            pulsar_ip,
            pulsar_topic,
            notifier_check_interval_seconds,
            wait_seconds_after_notify,
            before_callback=None,
            after_callback=None,
            **kwargs
    ):
        """
        Call back is only support none arg for now
        """
        self.session = session
        self.ip = pulsar_ip
        self.topic = pulsar_topic
        self.check_interval = notifier_check_interval_seconds
        self.wait_seconds_after_notify = wait_seconds_after_notify
        self.message = "start"
        self._running = False
        self._is_last_case = False
        self.before_callback = before_callback
        self.after_callback = after_callback
        self.cid = self.start()

    def update_notify_message(self, msg):
        self.message = msg

    def set_last_case(self):
        self._is_last_case = True

    def notify(self):
        import pulsar
        client = pulsar.Client(self.ip)
        producer = client.create_producer(self.topic)
        producer.send(self.message.encode('utf-8'))
        client.close()

    def should_notify(self):
        if (
                self.session.get_runner_count_by_status(RunnerStatus.WAITING)
                == self.session.get_expected_runner_count()
        ):
            return True

    def notify_with_retry(self):
        retry = 6
        for _ in range(retry):
            if (
                self.session.get_runner_count_by_status(RunnerStatus.RUNNING)
                == self.session.get_expected_runner_count()
            ):
                break
            self.notify()
            sleep(5)
        else:
            logger.warning("Not all runners started testing!!")

    @thread
    def start(self):
        logger.info("Starting Notifier")
        self._running = True
        while self._running:
            try:
                # make sure all pods complete all tests
                if self.should_notify():
                    if self.before_callback:
                        self.before_callback()
                    # check again to wait for all pods registered
                    # in case before_callback change pods
                    if self.should_notify():
                        self.notify_with_retry()
                    else:
                        continue
                    if self.after_callback:
                        self.after_callback()
                    if self._is_last_case:
                        break
                    sleep(self.wait_seconds_after_notify)
                    continue
                sleep(self.check_interval)
            except Exception as e:
                logger.exception("Error in notifier", exc_info=e)

    def stop(self):
        logger.info("Stopping notifier")
        self._running = False
        ThreadsManager().wait_for_complete([self.cid])
