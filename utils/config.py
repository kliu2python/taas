import os

import yaml

from singleton_decorator import singleton


@singleton
class Config:
    def __init__(self, config_path, encrypt_key=None):
        self.config_path = config_path
        self.encrypt_key = encrypt_key
        self._load_config()

    def _load_config(self):
        use_unencrypted = True
        if self.encrypt_key and os.path.exists(self.encrypt_key):
            try:
                import pickle
                from cryptography.fernet import Fernet

                with open(self.encrypt_key, "rb") as FILE:
                    key = pickle.load(FILE)
                    f = Fernet(key)

                with open(self.config_path, "rb") as FILE:
                    content = f.decrypt(FILE.read()).decode()
                    self.config = yaml.safe_load(content)
                    use_unencrypted = False
            except Exception:
                pass
        if use_unencrypted:
            with open(self.config_path) as FILE:
                self.config = yaml.safe_load(FILE)

        for key, value in self.config.items():
            self.__setattr__(key, value)
