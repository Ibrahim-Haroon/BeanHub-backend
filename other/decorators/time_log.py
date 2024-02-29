"""
This module contains a decorator that logs the time taken for a function to execute.
"""
import time
import logging
from src.django_beanhub.settings import DEBUG

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')


def time_log(func):
    """
    This decorator logs the time taken for a function to execute.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.debug(f"{func.__name__} time: {end_time - start_time}")
        return result

    return wrapper
