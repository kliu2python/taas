import os

from utils.config import Config


CONF_PATH = os.path.join(
    os.path.dirname(__file__),
    "config",
    "config.yaml"
)
KEY_PATH = os.path.join(
    os.path.dirname(__file__),
    "enobj"
)
CONF = Config(CONF_PATH, KEY_PATH).config
