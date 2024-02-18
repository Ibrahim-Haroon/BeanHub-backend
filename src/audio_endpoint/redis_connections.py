"""
This module contains helper functions that are used for connecting to Redis
"""
import redis
import time
import logging
from os import getenv as env
from dotenv import load_dotenv
from src.django_beanhub.settings import DEBUG

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


def connect_to_redis_temp_conversation_cache(

) -> redis.Redis:  # pragma: no cover
    """
    @rtype: redis.StrictRedis
    @return: redis client
    """
    while True:
        try:
            redis_client = redis.StrictRedis(
                host=env('REDIS_HOST'),
                port=env('REDIS_PORT'),
                db=0
            )
            logging.debug("Connected to conversation history")
            return redis_client
        except redis.exceptions.ConnectionError:
            logging.debug("Failed to connect to Redis. Retrying in 5 seconds...")
            time.sleep(5)


def connect_to_redis_embedding_cache(

) -> redis.Redis:  # pragma: no cover
    """
    @rtype: redis.StrictRedis
    @return: redis client
    """
    while True:
        try:
            redis_client = redis.StrictRedis(
                host=env('REDIS_HOST'),
                port=env('REDIS_PORT'),
                db=1
            )
            logging.debug("Connected to embedding cache")
            return redis_client
        except redis.exceptions.ConnectionError:
            logging.debug("Failed to connect to Redis. Retrying in 5 seconds...")
            time.sleep(5)


def connect_to_redis_temp_deal_cache(

) -> redis.Redis:  # pragma: no cover
    """
    @rtype: redis.StrictRedis
    @return: redis client
    """
    while True:
        try:
            redis_client = redis.StrictRedis(
                host=env('REDIS_HOST'),
                port=env('REDIS_PORT'),
                db=2
            )
            logging.debug("Connected to deal history")
            return redis_client
        except redis.exceptions.ConnectionError:
            logging.debug("Failed to connect to Redis. Retrying in 5 seconds...")
            time.sleep(5)