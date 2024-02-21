"""
This file is used to configure the app name for the audio_stream app.
"""
import logging
import time
from django.apps import AppConfig
from os import getenv as env
from dotenv import load_dotenv
from pika.exceptions import ConnectionClosed
from pika import BlockingConnection, ConnectionParameters

load_dotenv()


def connect_to_rabbitmq(
) -> BlockingConnection:
    """
    @rtype: BlockingConnection
    @return: rabbitmq connection
    """
    connection = None
    while not connection:
        try:
            connection = BlockingConnection(ConnectionParameters(
                env('RABBITMQ_HOST'),
            ))
        except Exception as e:
            logging.error("Failed to connect to RabbitMQ. Retrying...")
            time.sleep(2)

    return connection


class AudioStreamConfig(AppConfig):  # pragma: no cover
    """
    This class is used to configure the app name for the audio_stream app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.audio_stream"

    def __init__(
            self, app_name, app_module
    ) -> None:
        super().__init__(app_name, app_module)
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None

    def ready(
            self
    ) -> None:
        if env('DJANGO_RUNNING_TESTS') == 'True':
            logging.debug("Skipping connection setup during tests.")
            return

        self.rabbitmq_connection = connect_to_rabbitmq()
        self.rabbitmq_channel = self.rabbitmq_connection.channel()
