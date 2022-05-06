import os

from utils.cassandra import register_connection
from utils.config import Config


CONF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "config",
    "config.yaml"
)
CONF = Config(CONF_PATH).config
