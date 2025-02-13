import pika
from time import sleep

from benchmark.common.conf import CONF
from utils.logger import get_logger


LOGGER = get_logger()
QUEUE_NAME = "benchmark_queue"


class Worker:
    """
    Worker for consume data from rabbitmq, call_back should be have following
    signature:

    call_back(data)

    """
    def __init__(self, call_back):
        self.channel = None
        self.call_back = call_back

        self.init_message_queue()

    def init_message_queue(self):
        con_url = CONF.get("rabbitmq")
        if not con_url:
            raise Exception("Rabbitmq connection url must be specified")

        conn = pika.BlockingConnection(pika.URLParameters(con_url))
        self.channel = conn.channel()
        self.channel.queue_declare(QUEUE_NAME)
        self.channel.basic_qos(prefetch_count=1)

    # pylint: disable=unused-argument
    def _consume_call_back(self, ch, method, properties, body):
        try:
            data = body.decode()
            if data:
                self.call_back(data)
        except Exception as e:
            LOGGER.exception("Error when call consume callback", exc_info=e)
        finally:
            # If we can not receive the data, try to skip so ack the message
            # To provent the queue too long
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def _ensure_channel_open(self):
        try:
            if self.channel.is_closed:
                print("Channel is closed. Reconnecting...")
                self.init_message_queue()  # Reinitialize connection and channel
        except AttributeError:
            print("Channel not initialized. Reinitializing...")
            self.init_message_queue()

    def consume_message(self):
        while True:
            try:
                self._ensure_channel_open()
                self.channel.basic_consume(
                    queue=QUEUE_NAME,
                    on_message_callback=self._consume_call_back
                )
                LOGGER.info("Starting consumption...")
                self.channel.start_consuming()
            except pika.exceptions.ChannelWrongStateError:
                LOGGER.exception("Channel error. Reinitializing...")
                self.init_message_queue()
            except pika.exceptions.AMQPConnectionError:
                LOGGER.exception("Connection error. Retrying in 5 seconds...")
                sleep(5)
