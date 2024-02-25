import time
import logging
import threading
from queue import Queue
from os import getenv as env
from dotenv import load_dotenv
import pika
from src.django_beanhub.settings import DEBUG


LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


class RabbitMQConnectionPool:
    """
    This class is used to manage connections to RabbitMQ.
    """
    def __init__(
            self, max_size
    ) -> None:
        self.connections = Queue(maxsize=max_size)
        self.lock = threading.Lock()

        for _ in range(max_size):
            self.connections.put(self.create_new_connection())

    @staticmethod
    def create_new_connection(

    ) -> pika.BlockingConnection:
        """
        @rtype: BlockingConnection
        @return: new rabbitmq connection
        """
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    env('RABBITMQ_HOST'),
                ))
                logging.debug("Connected to RabbitMQ successfully.")
                return connection
            except Exception as e:
                logging.error(f"Failed to connect to RabbitMQ {e}. Retrying...")
                time.sleep(2)

    def get_connection(
            self
    ) -> pika.BlockingConnection:
        """
        @rtype: BlockingConnection
        @return: rabbitmq connection from pool (or new connection if pool is empty)
        """
        with self.lock:
            if self.connections.empty():
                return self.create_new_connection()
            return self.connections.get()
