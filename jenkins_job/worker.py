import pika
import time
import json

from apscheduler.schedulers.background import BackgroundScheduler
from jenkins_job.conf import CONF, QUEUE_NAME
from utils.logger import get_logger
from jenkins_job.manager import JenkinsJobs  # Adjust the import as needed

LOGGER = get_logger()


class RabbitMQWorker:
    """
    Worker that consumes tasks from RabbitMQ.

    Each task is expected to be a JSON string with the following keys:
      - job_name: a string representing the job to run (e.g., a job URL or name)
      - parameters: a dictionary of parameters to pass to the Jenkins build
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        """Initialize the connection and channel to RabbitMQ."""
        con_url = CONF.get("rabbitmq")
        if not con_url:
            raise Exception("RabbitMQ connection URL must be specified")
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(con_url)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=QUEUE_NAME, durable=True)
            self.channel.basic_qos(prefetch_count=1)
            LOGGER.info("Connected to RabbitMQ and declared queue %s", QUEUE_NAME)
        except Exception as e:
            LOGGER.exception("Failed to connect to RabbitMQ: %s", e)
            raise

    def _consume_callback(self, ch, method, properties, body):
        """
        Internal callback that decodes the message, extracts the task data,
        and calls execute_job_task() to run the Jenkins build.
        """
        try:
            data = body.decode("utf-8")
            if data:
                # Parse the task data from JSON.
                task = json.loads(data)
                job_name = task.get("job_name")
                nickname = task.get("nickname")
                parameters = task.get("parameters", {})
                LOGGER.info("Received task for job: %s", job_name)
                # Instantiate JenkinsJobs and execute the job task.
                jenkins_instance = JenkinsJobs()
                result = jenkins_instance.execute_job_task(
                    job_name, parameters, nickname
                )
                LOGGER.info("Execution result: %s", result)
        except Exception as e:
            LOGGER.exception("Error processing message: %s", e)
        finally:
            # Acknowledge the message regardless of success to avoid buildup.
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        """
        Starts consuming messages from the queue. If a connection failure
        occurs, it will attempt to reconnect.
        """
        while True:
            try:
                self.channel.basic_consume(
                    queue=QUEUE_NAME,
                    on_message_callback=self._consume_callback
                )
                LOGGER.info("Starting consuming messages...")
                self.channel.start_consuming()
            except pika.exceptions.AMQPConnectionError as e:
                LOGGER.exception("Connection error: %s", e)
                LOGGER.info("Reconnecting in 5 seconds...")
                time.sleep(5)
                self.connect()
            except Exception as e:
                LOGGER.exception("Unexpected error: %s", e)
                time.sleep(5)


def job_task():
    """Fetch and store the Jenkins job structure."""
    JenkinsJobs().fetch_and_store_job_structure()


# Scheduler Setup for Background Task
def start_scheduler():
    """Set up the scheduler to periodically fetch and store job structure."""

    LOGGER.info("creating the scheduler job")
    scheduler = BackgroundScheduler()
    # Schedule the job to run every hour
    scheduler.add_job(job_task, 'interval', minutes=5)
    scheduler.start()
    LOGGER.info("Scheduler started to update Jenkins job structure.")

    try:
        # Keep the scheduler running
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


# Example usage:
if __name__ == "__main__":
    worker = RabbitMQWorker()
    worker.start_consuming()

    start_scheduler()
