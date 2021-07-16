from concurrent.futures import ProcessPoolExecutor
from time import sleep

import scale.variables as variables
from scale.metrics.elasticsearch import ElasticSearchMonitor
from utils.logger import get_logger

logger = get_logger()


def monitor():
    restart = True
    elastic_search_engine = variables.config.get("elastic_search_engine")
    elastic_search_credential = variables.config.get(
        "elastic_search_credential"
    )
    sleep_time = 3600
    while True:
        try:
            if restart:
                ElasticSearchMonitor(
                    elastic_search_engine=elastic_search_engine,
                    elastic_search_credential=elastic_search_credential
                ).start()
                restart = False
                sleep_time = 3600
        except Exception as e:
            logger.exception("Error in Monitor restarting", exc_info=e)
            restart = True
            sleep_time = 10
        sleep(sleep_time)


if __name__ == "__main__":
    logger.info("Starting ElasticSearch Monitor")
    with ProcessPoolExecutor(max_workers=1) as pool:
        pool.submit(monitor)
