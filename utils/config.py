import yaml
from singleton_decorator import singleton


@singleton
class Config:
    def __init__(self, config_path):
        self.config_path = config_path
        self._load_config()

    def _load_config(self):
        with open(self.config_path) as FILE:
            self.config = yaml.safe_load(FILE)

        for key, value in self.config.items():
            self.__setattr__(key, value)
