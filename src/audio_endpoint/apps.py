"""
This file is used to configure the app name for the audio_endpoint app.
"""
from django.apps import AppConfig
from src.vector_db.aws_database_auth import connection_string
import src.audio_endpoint.redis_connections as redis
from src.vector_db.aws_sdk_auth import get_secret
from os import getenv as env
import boto3
import psycopg2.pool
from dotenv import load_dotenv
from pika import BlockingConnection, ConnectionParameters

load_dotenv()


class AudioEndpointConfig(AppConfig):
    """
    This class is used to configure the app name for the audio_endpoint app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.audio_endpoint"

    def __init__(
            self, app_name, app_module
    ) -> None:
        super().__init__(app_name, app_module)
        self.s3 = None
        self.bucket_name = None
        self.conversation_cache = None
        self.deal_cache = None
        self.embedding_cache = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.connection_pool = None

    def ready(
            self
    ) -> None:
        ####################
        ## AWS CONNECTION ##
        get_secret()
        self.s3 = boto3.client('s3')
        self.bucket_name = env('S3_BUCKET_NAME')
        ######################
        ## REDIS CONNECTION ##
        self.conversation_cache = redis.connect_to_redis_temp_conversation_cache()
        self.deal_cache = redis.connect_to_redis_temp_deal_cache()
        self.embedding_cache = redis.connect_to_redis_embedding_cache()
        #########################
        ## RABBITMQ CONNECTION ##
        self.rabbitmq_connection = BlockingConnection(ConnectionParameters(env('RABBITMQ_HOST')))
        self.rabbitmq_channel = self.rabbitmq_connection.channel()
        ###########################
        ## POSTGRESQL CONNECTION ##
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())
        ###########################
