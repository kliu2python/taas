import utils.rest as rest_lib
from dhub.hosts.host import Host


class Master(Host):
    def __init__(self, config):
        self.config = config
        self.ips = [config.get("host_ip")]
        self.load_mode = (
            config.get("master_config", {}).get("running_mode", "load-blancer")
        )

    @property
    def running_mode(self):
        return "master"

    def register_ip(self, ip):
        self.ips.append(ip)

    def _get_ip(self, method="revolver"):
        ip_to_ret = None
        if method in ["revolver"]:
            ip_to_ret = self.ips.pop(0)
            self.ips.append(ip_to_ret)
        return ip_to_ret

    def get_device_host_ip(self):
        if self.load_mode in ["load-blancer"]:
            return self._get_ip()
        print(f"invalided load blancer mode {self.load_mode}")

    @staticmethod
    def get_device_remote(ip, platform_id):
        ret = rest_lib.rest_call(
            ip, 8000, "/getdevice", "GET", {"platform_id": platform_id}
        )
        if ret:
            return ret.decode()
