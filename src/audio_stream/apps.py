"""
This file is used to configure the app name for the audio_stream app.
"""
from django.apps import AppConfig
from os import getenv as env
from dotenv import load_dotenv
from pika import BlockingConnection, ConnectionParameters

load_dotenv()


class AudioStreamConfig(AppConfig):
    """
    This class is used to configure the app name for the audio_stream app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.audio_stream"

    def ready(
            self
    ) -> None:
        self.rabbitmq_connection = BlockingConnection(ConnectionParameters(env('RABBITMQ_HOST')))
        self.rabbitmq_channel = self.rabbitmq_connection.channel()