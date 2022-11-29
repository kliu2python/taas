import re

from upgrade.caches import StaticsCache
from utils.logger import get_logger


CACHE = StaticsCache()
LOGGER = get_logger()
KEY_FILTER = re.compile(r"\/(.*)\/v1\/(\w+)")


def count_access(resp):
    try:
        method = resp.json_module.request.method
        matches = KEY_FILTER.search(resp.json_module.request.path)
        if matches:
            key = f"{matches.group(1)}_{matches.group(2)}_{method}"
            CACHE.incr(key, 1)
    except Exception as e:
        LOGGER.debug("Error when counting access", exc_info=e)

    return resp

