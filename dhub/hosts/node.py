from time import sleep
from threading import Thread

import utils.rest as rest_lib


class Node:
    def __init__(self, config):
        self.ip = config.get("host_ip")
        self.config = config
        self.register_to_master_thread()

    @property
    def running_mode(self):
        return "node"

    def register_to_master(self):
        res = rest_lib.rest_call(
            self.config.get("master_ip"),
            8000,
            "/internal/registernodeip",
            "GET",
            {"ip": self.ip}
        )
        res = res.decode()
        if "SUCCESS" not in res:
            print(f"Error when register node ip, error: {res}")

    def _register_to_master_thread_func(self):
        while True:
            self.register_to_master()
            sleep(
                self.config.get("node_config", {})
                .get("register_interval", 30) * 60
            )

    def get_device_host_ip(self):
        return self.ip

    def register_to_master_thread(self):
        thread = Thread(target=self._register_to_master_thread_func)
        thread.start()
        print("node register thread started")
