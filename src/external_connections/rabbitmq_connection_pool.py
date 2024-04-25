""""
This module contains the RabbitMQConnectionPool class, which is used to manage connections to RabbitMQ. Currently,
it is not being used since pika is not multi-thread safe.
"""
import time
import logging
import threading
from queue import Queue
from os import getenv as env
from dotenv import load_dotenv
import pika
from other.decorators.time_log import time_log
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
        self._connections = Queue(maxsize=max_size)
        self.__lock = threading.Lock()
        self._max_size = max_size

        for _ in range(max_size):
            self._connections.put(self._create_new_connection())

    @staticmethod
    def _create_new_connection(

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

    @time_log
    def _refill_connection_pool(
            self
    ) -> None:
        """
        @rtype: None
        @return: nothing (creates a new connection and adds it to the pool)
        """
        for _ in range(self._max_size):
            self._connections.put(self._create_new_connection())

    def get_connection(
            self
    ) -> pika.BlockingConnection:
        """
        This functino is used to get a rabbitmq connection from the pool.
        @rtype: BlockingConnection
        @return: rabbitmq connection from pool (or new connection if pool is empty)
        """
        with self.__lock:
            if self._connections.empty():
                self._refill_connection_pool()
            return self._connections.get()
