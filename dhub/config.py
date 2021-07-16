import os

import yaml


config_dir = os.path.join(
    os.path.dirname(__file__),
    "configs"
)

configs = {
    "device": "device_config.yml",
    "host": "host_config.yml"
}

_config = None


def _load_config():
    """
    Internal method for loading config, please always use get_config to get
    config
    :return: config dict
    """
    config_dict = {}
    for config_name, config_file in configs.items():
        config_path = os.path.join(config_dir, config_file)
        print(f"Loading config {config_path}")
        with open(config_path) as FILE:
            config_loaded = yaml.safe_load(FILE)
            config_dict[config_name] = Config(
                config_name, config_loaded.get(config_name)
            )
    return config_dict


def get_config(key: str=None):
    """
    user should always use this one to get config. this will grantee config load
    :param key: config type: device or host
    :return:
    """
    global _config
    _config_ret = None
    if _config is None:
        _config = _load_config()
    if key is not None:
        _config_ret = _config.get(key)
        if _config_ret is None:
            raise ValueError("Please specify correct key value, either device"
                             "or host")
    return _config_ret


class Config:
    def __init__(self, config_type, config_loaded):
        """
        Config object for all configs, it will only load once after system start
        """
        self.config_loaded = config_loaded
        self.__class__ = globals()[f"{config_type.capitalize()}Config"]


class DeviceConfig(Config):
    def get_config_by_platform_id(self, platform_id):
        """
        Please make sure the platform id is unique in the config file.
        if we have duplicate item, this will only return the first one.
        :param platform_id: str, platform id to search
        :return:
        """
        if self.config_loaded is not None:
            for config in self.config_loaded.get("platform_config"):
                if config.get("platform_id") in [platform_id]:
                    return config
        else:
            raise ValueError("Make sure config file has correct format")

    def get_platform_configs(self):
        return self.config_loaded.get("platform_config")

    def get_global_configs(self):
        return self.config_loaded.get("global")


class HostConfig(Config):
    def get_host_configs(self):
        return self.config_loaded
