import os

from utils.config import Config


CONF_PATH = os.path.join(os.path.dirname(__file__), "config.yml")
CONF = Config(CONF_PATH).config
QUEUE_NAME = "jenkins_queue"
MONGODB_INFO = CONF.get("mongodb", {})
