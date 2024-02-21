"""
This file is used to configure the app name for the audio_endpoint app.
"""
import time
import logging
import redis
from django.apps import AppConfig
from src.vector_db.aws_database_auth import connection_string
from src.vector_db.aws_sdk_auth import get_secret
from os import getenv as env
import boto3
import psycopg2.pool
from dotenv import load_dotenv
from pika.exceptions import ConnectionClosed
from pika import BlockingConnection, ConnectionParameters
from src.django_beanhub.settings import DEBUG

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


def connect_to_s3(

) -> boto3.client:
    """
    @rtype: boto3.client
    @return: s3 client
    """
    try:
        client = boto3.client('s3')
        logging.debug("Connected to S3 successfully.")
        return client
    except boto3:
        logging.debug("Failed to connect to S3. Retrying...")
        time.sleep(2)


def connect_to_redis_cache(
        db: int
) -> redis.Redis | None:
    """
    @rtype: redis.StrictRedis
    @return: redis client
    """
    while True:
        try:
            redis_client = redis.StrictRedis(
                host=env('REDIS_HOST'),
                port=env('REDIS_PORT'),
                db=db
            )
            logging.debug("Connected to cache successfully.")
            return redis_client
        except redis.exceptions.ConnectionError:
            logging.debug("Failed to connect to Redis. Retrying...")
            time.sleep(2)


def connect_to_rabbitmq(
) -> BlockingConnection:
    """
    @rtype: BlockingConnection
    @return: rabbitmq connection
    """
    while True:
        try:
            connection = BlockingConnection(ConnectionParameters(
                env('RABBITMQ_HOST'),
            ))
            logging.debug("Connected to RabbitMQ successfully.")
            return connection
        except ConnectionClosed:
            print("Failed to connect to RabbitMQ. Retrying...")
            time.sleep(2)


def connect_to_postgresql(

) -> psycopg2.pool.SimpleConnectionPool:
    """
    @rtype: psycopg2.pool.SimpleConnectionPool
    @return: postgresql connection pool
    """
    try:
        pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())
        logging.debug("Connected to PostgreSQL successfully.")
        return pool
    except psycopg2.Error:
        logging.debug("Failed to connect to PostgreSQL. Retrying...")
        time.sleep(2)


class AudioEndpointConfig(AppConfig):  # pragma: no cover
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
        if env('DJANGO_RUNNING_TESTS') == 'True':
            logging.debug("Skipping connection setup during tests.")
            return

        ####################
        ## AWS CONNECTION ##
        get_secret()
        self.s3 = connect_to_s3()
        self.bucket_name = env('S3_BUCKET_NAME')
        ######################
        ## REDIS CONNECTION ##
        self.conversation_cache = connect_to_redis_cache(0)
        self.deal_cache = connect_to_redis_cache(1)
        self.embedding_cache = connect_to_redis_cache(2)
        #########################
        ## RABBITMQ CONNECTION ##
        self.rabbitmq_connection = connect_to_rabbitmq()
        self.rabbitmq_channel = self.rabbitmq_connection.channel()
        ###########################
        ## POSTGRESQL CONNECTION ##
        self.connection_pool = connect_to_postgresql()
        ###########################
