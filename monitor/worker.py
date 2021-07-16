from time import sleep

from monitor.metrics.ftc import FtcMonitor
from utils.logger import get_logger

logger = get_logger()


def monitor():
    restart = True
    sleep_time = 3600
    while True:
        try:
            if restart:
                FtcMonitor().start()
                restart = False
                sleep_time = 3600
        except Exception as e:
            logger.exception("Error in Monitor restarting", exc_info=e)
            restart = True
            sleep_time = 10
        sleep(sleep_time)


if __name__ == "__main__":
    logger.info("Starting Monitor")
    monitor()
