from upgrade.caches import StaticsCache
from utils.logger import get_logger

cache = StaticsCache()
logger = get_logger()
PREFIX = "__sys__"


def update_total_upgrades():
    try:
        cache.incr("total_upgrades", 1, PREFIX)
    except Exception as e:
        logger.exception(f"ignoring error {e}")


def update_total_build_query():
    try:
        cache.incr("total_build_query", 1, PREFIX)
    except Exception as e:
        logger.exception(f"ignoring error {e}")
