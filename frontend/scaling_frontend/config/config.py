import os

import yaml
from singleton_decorator import singleton


@singleton
class Config:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        curr_path = os.path.dirname(__file__)
        config_path = os.path.join(
            curr_path, "config", "frontend_config.yaml"
        )
        with open(config_path) as FILE:
            self.config = yaml.safe_load(FILE)

        for key, value in self.config.items():
            self.__setattr__(key, value)
