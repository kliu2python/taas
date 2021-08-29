import os

from utils.cassandra import register_connection
from utils.config import Config
from utils.logger import get_logger

logger = get_logger()

config_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "config",
    "config.yaml"
)
config = Config(config_path).config
db = config.get("db", {})
datacenter = db.pop("dc", "dc1")
cass_session = register_connection(name="taas", **db)
