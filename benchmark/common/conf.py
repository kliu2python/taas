import os

from utils.cassandra import register_connection
from utils.config import Config


CONF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "config",
    "config.yaml"
)
CONF = Config(CONF_PATH).config
_db = CONF.get("db", {})
DATACENTER = _db.pop("dc", "dc1")

cass_session = register_connection(name="taas", **_db)
