import prometheus_client
from singleton_decorator import singleton


@singleton
class MetricsPushGateway:
    def __init__(self, gateway_ip):
        self.gateway_ip = gateway_ip
        self.registry = prometheus_client.CollectorRegistry()

    def push_gauge(self, value, name, description, job):
        gauge = prometheus_client.Gauge(name, description, self.registry)
        gauge.set_to_current_time()
        gauge.set(value)
        prometheus_client.push_to_gateway(
            self.gateway_ip, job=job, registry=self.registry
        )
