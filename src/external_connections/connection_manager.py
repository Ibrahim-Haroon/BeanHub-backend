"""
This module is used to manage connections to external services such as AWS, PostgreSQL, etc.
"""
import time
import logging
import threading
import redis
from os import getenv as env
import boto3
import psycopg2.pool
from dotenv import load_dotenv
import pika
from typing import Optional
from src.django_beanhub.settings import DEBUG
from src.external_connections.rabbitmq_connection_pool import RabbitMQConnectionPool
from src.vector_db.aws_database_auth import connection_string
from src.vector_db.aws_sdk_auth import get_secret

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


class ConnectionManager():
    """
    This singleton class is used to manage connections to external services such as RabbitMQ, PostgreSQL, etc.
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
        self.__rabbitmq_connection_pool = None
        self.postgres_max_connections = 10
        self.rabbitmq_max_connections = 5

    @staticmethod
    def connect(

    ) -> 'ConnectionManager':
        """
        This method is used to get the connection manager instance.
        @rtype: ConnectionManager
        @return: connection manager instance
        """
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
        self.__rabbitmq_pool = self.__connect_to_rabbitmq_pool()
        ###########################
        ## POSTGRESQL CONNECTION ##
        self.__connection_pool = self.__connect_to_postgresql()
        ###########################

    def s3(
            self
    ) -> boto3.client:
        """
        This method is used to get the s3 client.
        @rtype: boto3.client
        @return: s3 client
        """
        return self.__s3

    def bucket_name(
            self
    ) -> str:
        """
        This method is used to get the s3 bucket name.
        @rtype: str
        @return: s3 bucket name
        """
        return self.__bucket_name

    def redis_cache(
            self, _type_: str
    ) -> redis.Redis:
        """
        This method is used to get the cache for conversation, deal, or embedding.
        @rtype: redis.Redis
        @return: cache for conversation, deal, or embedding
        """
        cache_name = f'_ConnectionManager__{_type_}_cache'
        return getattr(self, cache_name)

    def rabbitmq_connection(
            self
    ) -> pika.BlockingConnection:
        """
        This method is used to get the rabbitmq connection.
        @rtype: BlockingConnection
        @return: rabbitmq connection
        """
        return self.__rabbitmq_pool.get_connection()

    def connection_pool(
            self
    ) -> psycopg2.pool.SimpleConnectionPool:
        """
        This method is used to get the postgresql connection pool.
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
            except Exception as e:
                logging.debug(f"Failed to connect to S3 {e}. Retrying...")
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
            except redis.exceptions.ConnectionError as e:
                logging.debug(f"Failed to connect to Redis {e}. Retrying...")
                time.sleep(2)

    def __connect_to_rabbitmq_pool(
            self
    ) -> RabbitMQConnectionPool:
        """
        @rtype: BlockingConnection
        @return: rabbitmq connection pool
        """
        return RabbitMQConnectionPool(self.rabbitmq_max_connections)

    def __connect_to_postgresql(
            self
    ) -> psycopg2.pool.SimpleConnectionPool:
        """
        @rtype: psycopg2.pool.SimpleConnectionPool
        @return: postgresql connection pool
        """
        while True:
            try:
                pool = psycopg2.pool.SimpleConnectionPool(1, self.postgres_max_connections, connection_string())
                logging.debug("Connected to PostgreSQL successfully.")
                return pool
            except psycopg2.Error as e:
                logging.debug(f"Failed to connect to PostgreSQL {e}. Retrying...")
                time.sleep(2)


if __name__ == '__main__':  # pragma: no cover
    ConnectionManager.connect()
    print("Connected to all services successfully.")
