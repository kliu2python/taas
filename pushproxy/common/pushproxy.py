import prometheus_client

from utils.logger import get_logger


LOGGER = get_logger()


def remove_push_gateway(ip, job, grouping_key=None):
    try:
        prometheus_client.delete_from_gateway(ip, job, grouping_key)
    except Exception as e:
        LOGGER.exception("Error when cleanup push gateway", exc_info=e)


class PushGateway:
    POOL = {}
    
    def __init__(self, push_gateway_ip, job, grouping_key=None):
        self.push_gateway_ip = push_gateway_ip
        self.job = job
        self.grouping_key = grouping_key
        PushGateway.POOL[job] = self

    def cleanup(self):
        LOGGER.info(f"Stopping metrics {self.job}")
        remove_push_gateway(
            self.push_gateway_ip,
            job=self.job,
            grouping_key=self.grouping_key
        )
        PushGateway.POOL.pop(self.job)
    
    @staticmethod
    def get_pushproxy(job):
        return PushGateway.POOL.get(job)

    @staticmethod
    def _get_gauge(label, description, label_names, registry):
        return prometheus_client.Gauge(
            label,
            description,
            labelnames=label_names,
            registry=registry
        )

    def push(self, data, data_time=None):
        """
        data with labels:
        [
            {
                category: bp_benchmark_cpu
                labels: [{
                    label_name1: label1,
                    label_name2: label2
                }]
                value: [xxx]
                description: "bp benchmark cpu"
                time: unix_time, time.time() // float
            }
        ]
        """
        registry = prometheus_client.CollectorRegistry()
        created_gauges = {}
        for counter_value in data:
            try:
                if counter_value is not None:
                    labels = counter_value.get("labels", [])
                    category = counter_value.get("category")
                    if category not in created_gauges:
                        gauge = self._get_gauge(
                            category,
                            counter_value.get("description"),
                            label_names=list(labels[0].keys()),
                            registry=registry
                        )
                        created_gauges[category] = gauge
                    else:
                        gauge = created_gauges.get(category)
                    values = counter_value.get("values", [])
                    if len(labels) > 0:
                        for label, value in zip(labels, values):
                            if data_time:
                                gauge.labels(**label).set(data_time)
                            else:
                                gauge.labels(**label).set_to_current_time()
                            gauge.labels(**label).set(value)
                else:
                    raise ValueError("counter_value must be a dict")
            except Exception as e:
                LOGGER.exception(
                    f"Error when collect data for:{counter_value}",
                    exc_info=e
                )
        self._push(registry)

    def _push(self, registry):
        prometheus_client.push_to_gateway(
            self.push_gateway_ip,
            job=self.job,
            registry=registry,
            grouping_key=self.grouping_key
        )
