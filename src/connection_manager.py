import time
import logging
import threading
import redis
from src.vector_db.aws_database_auth import connection_string
from src.vector_db.aws_sdk_auth import get_secret
from os import getenv as env
import boto3
import psycopg2.pool
from dotenv import load_dotenv
import pika
from src.django_beanhub.settings import DEBUG
from typing import Optional

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


class ConnectionManager():  # pragma: no cover
    """
    This class is used to manage connections to external services such as RabbitMQ, PostgreSQL, etc.
    """
    __lock: threading.Lock = threading.Lock()
    __instance: Optional['ConnectionManager'] = None

    def __init__(
            self
    ) -> None:
        self.__s3 = None
        self.__bucket_name = None
        self.__conversation_cache = None
        self.__deal_cache = None
        self.__embedding_cache = None
        self.__rabbitmq_connection = None
        self.__rabbitmq_channel = None
        self.__connection_pool = None

    @staticmethod
    def connect(

    ) -> 'ConnectionManager':
        with ConnectionManager.__lock:
            if not ConnectionManager.__instance:
                ConnectionManager.__instance = ConnectionManager()
                ConnectionManager.__instance.__connect()

            return ConnectionManager.__instance

    def __connect(
            self
    ) -> None:
        ####################
        ## AWS CONNECTION ##
        get_secret()
        self.__s3 = self.__connect_to_s3()
        self.__bucket_name = env('S3_BUCKET_NAME')
        ######################
        ## REDIS CONNECTION ##
        self.__conversation_cache = self.__connect_to_redis_cache(0)
        self.__deal_cache = self.__connect_to_redis_cache(1)
        self.__embedding_cache = self.__connect_to_redis_cache(2)
        #########################
        ## RABBITMQ CONNECTION ##
        self.__rabbitmq_connection = self.__connect_to_rabbitmq()
        self.__rabbitmq_channel = self.__rabbitmq_connection.channel()
        ###########################
        ## POSTGRESQL CONNECTION ##
        self.__connection_pool = self.__connect_to_postgresql()
        ###########################

    def s3(
            self
    ) -> boto3.client:
        """
        @rtype: boto3.client
        @return: s3 client
        """
        return self.__s3

    def bucket_name(
            self
    ) -> str:
        """
        @rtype: str
        @return: s3 bucket name
        """
        return self.__bucket_name

    def redis_cache(
            self, _type_: str
    ) -> redis.Redis:
        """
        @rtype: redis.Redis
        @return: cache for conversation, deal, or embedding
        """
        cache_name = f'_ConnectionManager__{_type_}_cache'
        return getattr(self, cache_name)

    def rabbitmq_connection(
            self
    ) -> pika.BlockingConnection:
        """
        @rtype: BlockingConnection
        @return: rabbitmq connection
        """
        return self.__rabbitmq_connection

    def rabbitmq_channel(
            self
    ) -> pika.adapters.blocking_connection.BlockingChannel:
        """
        @rtype: None
        @return: rabbitmq channel
        """
        return self.__rabbitmq_channel

    def connection_pool(
            self
    ) -> psycopg2.pool.SimpleConnectionPool:
        """
        @rtype: psycopg2.pool.SimpleConnectionPool
        @return: postgresql connection pool
        """
        return self.__connection_pool

    @staticmethod
    def __connect_to_s3(

    ) -> boto3.client:
        """
        @rtype: boto3.client
        @return: s3 client
        """
        while True:
            try:
                client = boto3.client('s3')
                logging.debug("Connected to S3 successfully.")
                return client
            except boto3:
                logging.debug("Failed to connect to S3. Retrying...")
                time.sleep(2)

    @staticmethod
    def __connect_to_redis_cache(
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

    @staticmethod
    def __connect_to_rabbitmq(
    ) -> pika.BlockingConnection:
        """
        @rtype: BlockingConnection
        @return: rabbitmq connection
        """
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    env('RABBITMQ_HOST'),
                ))
                logging.debug("Connected to RabbitMQ successfully.")
                return connection
            except Exception as e:
                logging.error("Failed to connect to RabbitMQ. Retrying...")
                time.sleep(2)

    @staticmethod
    def __connect_to_postgresql(

    ) -> psycopg2.pool.SimpleConnectionPool:
        """
        @rtype: psycopg2.pool.SimpleConnectionPool
        @return: postgresql connection pool
        """
        while True:
            try:
                pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())
                logging.debug("Connected to PostgreSQL successfully.")
                return pool
            except psycopg2.Error:
                logging.debug("Failed to connect to PostgreSQL. Retrying...")
                time.sleep(2)


if __name__ == '__main__':
    ConnectionManager.connect()
    print("Connected to all services successfully.")
