import os

import yaml


_CONF = {}
CONF_DIR = os.path.join(os.path.expanduser("~"), ".taas")
CONF_PATH = os.path.join(CONF_DIR, "taas.conf")
CACHE_DIR = os.path.join(CONF_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
DEFAULT_BACKEND = "10.160.83.213"


def init_config(args=None):
    os.makedirs(CONF_DIR, exist_ok=True)
    with open(CONF_PATH, "w") as F:
        yaml.safe_dump(
            {
                "server_ip": args.ip if args else DEFAULT_BACKEND
            }, F
        )
    print("Config Initialized")


def load_config():
    if os.path.exists(CONF_PATH):
        with open(CONF_PATH) as F:
            global _CONF
            _CONF = yaml.safe_load(F)
    else:
        init_config()


def get_config():
    return _CONF
