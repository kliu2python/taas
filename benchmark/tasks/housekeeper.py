from time import sleep

from benchmark.tasks.lifecycle import house_keeping
from utils.logger import get_logger


LOGGER = get_logger()


def start_house_keeper():
    LOGGER.info("Starting house keeper")
    while True:
        try:
            house_keeping()
        except Exception as e:
            LOGGER.exception("error when do house keeping", exc_info=e)
        sleep(5)


if __name__ == "__main__":
    start_house_keeper()
