def get_host(config):
    if config.get("master_ip") in ["localhost", "127.0.0.1"]:
        print("Running as master host")
        from dhub.hosts.master import Master
        return Master(config)
    print("Running as node host")
    from dhub.hosts.node import Node
    return Node(config)


class Host:
    def get_device_host_ip(self):
        raise NotImplementedError
