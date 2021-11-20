import re
from time import sleep

import prometheus_client
import requests

from scale.common.variables import config
from utils.logger import get_logger
from utils.threads import thread_run, ThreadsManager

logger = get_logger()


class SnmpMetrics:
    re_data = re.compile(r"^(?!#)(.*?)({(.*?)})?\s(.*?)$")

    def __init__(
            self,
            data,
    ):
        logger.info("Starting SNMP Metrics")
        self.target = data.get("command_log_targets")[-1].get("ssh_ip")
        self.module = data.get("module", "fortigate")
        self.exporter_url = (
            f"http://{config.get('snmp_exporter_ip')}/snmp?"
            f"target={self.target}"
            f"&module={self.module}"
        )
        self.session_id = data.get("session_id", "snmp_agent")
        self.registry = prometheus_client.CollectorRegistry()
        self.gauges = {}
        self.running = False
        self.cid = None
        self.job = f"snmp-{self.session_id}"
        self.start()

    def get_data(self):
        resp = requests.get(url=self.exporter_url)
        data = resp.content.decode()
        data_dicts = []
        if data:
            data = data.split("\n")
            if len(data) > 0 and data[0].startswith("#"):
                for d in data:
                    if not d or d.startswith("#"):
                        continue
                    matches = self.re_data.search(d).groups()
                    if len(matches) != 4:
                        logger.error(
                            f"matches data_lenth is not 2 or 3, "
                            f"it is {len(matches)}"
                        )
                        continue
                    d_dict = {
                        "counter": matches[0],
                        "label": matches[2],
                        "value": matches[3]
                    }

                    data_dicts.append(d_dict)
        self.upload_data(data_dicts)

    def register(self, data):
        if not self.gauges:
            for d in data:
                gauge_name = d.get("counter")
                if gauge_name not in self.gauges:
                    gauge = prometheus_client.Gauge(
                        gauge_name, "",
                        labelnames=[gauge_name],
                        registry=self.registry
                    )
                    self.gauges[gauge_name] = gauge

    @staticmethod
    def parse_label(label_str):
        labels = {}
        if label_str:
            if "," in label_str:
                label = label_str.split(",")
            else:
                label = [label_str]
            for lb in label:
                lb = lb.split("=")
                if len(lb) == 2:
                    labels[lb[0].strip("\"")] = lb[1].strip("\"")
        return labels

    def upload_data(self, data):
        self.register(data)
        registry = prometheus_client.CollectorRegistry()
        created = {}
        for d in data:
            counter = d["counter"]
            label = self.parse_label(d["label"])
            label["target"] = self.target
            if counter in created:
                gauge = created.get(counter)
            else:
                gauge = prometheus_client.Gauge(
                    counter, "",
                    labelnames=label.keys(),
                    registry=registry
                )
            created[counter] = gauge
            gauge.labels(**label).set_to_current_time()
            gauge.labels(**label).set(float(d["value"]))
        prometheus_client.push_to_gateway(
            config.get("pushgateway_ip", "10.160.83.213:9091"),
            job=self.job,
            registry=registry
        )

    def _start(self):
        self.running = True
        while self.running:
            try:
                self.get_data()
                sleep(config.get("pulling_interval", 10))
            except Exception as e:
                logger.exception("Error for Snmp get data", exc_info=e)

    def start(self):
        self.cid = thread_run(self._start)

    def stop(self):
        logger.info(f"Stopping Snmp metrics {self.module}")
        self.running = False
        try:
            prometheus_client.delete_from_gateway(
                config.get("pushgateway_ip"),
                job=self.job
            )
        except Exception as e:
            logger.exception("error when stop snmp metrics", exc_info=e)
        if self.cid:
            ThreadsManager().wait_for_complete([self.cid])


if __name__ == "__main__":
    snmp = SnmpMetrics({"command_log_targets": [{"ssh_ip": "10.65.13.140"}]})
    snmp.start()
    sleep(3600)
    # sleep(30)
    # snmp.stop()
