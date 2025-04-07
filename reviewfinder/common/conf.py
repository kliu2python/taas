import os

from utils.config import Config


CONF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "config.yml"
)
CONF = Config(CONF_PATH).config
_db = CONF.get("db", {})
DATACENTER = _db.pop("dc", "dc1")
