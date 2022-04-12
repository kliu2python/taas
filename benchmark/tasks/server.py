from benchmark.tasks.consumers.fortigate import consume_data
from benchmark.tasks.worker import Worker
from utils.logger import get_logger


LOGGER = get_logger()


if __name__ == "__main__":
    LOGGER.info("Starting worker for consume message")
    Worker(consume_data).consume_message()
