# pylint: disable=too-many-arguments
from time import sleep

import prometheus_client
from utils.config import Config
from utils.logger import get_logger
from utils.threads import thread_run, ThreadsManager

logger = get_logger()


class Metrics:
    def __init__(
            self,
            metrics,
            job,
            collecting_class,
            grouping_key=None,
            config_path=None,
            interval_seconds=None
    ):
        self.config = Config(config_path)
        self._running = False
        self.grouping_key = grouping_key
        self.metrics = metrics
        self.job = job
        self.collecting_class = collecting_class
        self.cid = None
        if interval_seconds:
            self.interval = interval_seconds
        else:
            self.interval = self.config.pulling_interval

    def _start(self):
        logger.info(f"Metrics {self.__class__.__name__} started")
        self._running = True
        while self._running:
            try:
                self._run()
            except Exception as e:
                logger.exception("Error when collect metrics:", exc_info=e)
            sleep(self.interval)

    def start_async(self):
        self.cid = thread_run(self._start)

    def start(self):
        self._start()

    def stop(self):
        logger.info(f"Stopping metrics {self.__class__.__name__}")
        self._running = False
        try:
            prometheus_client.delete_from_gateway(
                self.config.pushgateway_ip,
                job=self.job,
                grouping_key=self.grouping_key
            )
            self.collecting_class.quit()
        except Exception:
            pass
        if self.cid:
            ThreadsManager().wait_for_complete([self.cid])

    @staticmethod
    def _get_gauge(label, description, registry, label_names):
        return prometheus_client.Gauge(
            label,
            description,
            labelnames=label_names,
            registry=registry
        )

    def _run(self):
        self._push(self._collect())

    def _collect(self):
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
        registry = prometheus_client.CollectorRegistry()
        for label, value in self.metrics.items():
            try:
                counter_value = getattr(
                    self.collecting_class, self.metrics.get(label).get("method")
                )(**self.metrics.get(label).get("args", {}))
                if counter_value is not None:
                    gauge = self._get_gauge(
                        label,
                        value.get("description"),
                        registry,
                        value.get("labels", [])
                    )
                    if isinstance(counter_value, list):
                        for cv in counter_value:
                            labels = cv.get("labels", {})
                            gauge.labels(**labels).set_to_current_time()
                            gauge.labels(**labels).set(cv.get("value"))
                    else:
                        gauge.set_to_current_time()
                        gauge.set(counter_value)
            except Exception as e:
                logger.exception(
                    f"Error when collect data for label:{label}, data:{value}",
                    exc_info=e
                )
        return registry

    def _push(self, registry):
        prometheus_client.push_to_gateway(
            self.config.pushgateway_ip,
            job=self.job,
            registry=registry,
            grouping_key=self.grouping_key
        )
