import time
import json
import queue
import redis
import logging
import psycopg2
import threading
import numpy as np
from os import path
import psycopg2.pool
from io import StringIO
from pgvector.psycopg2 import register_vector
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.embeddings_api import openai_embedding_api
from src.vector_db.aws_database_auth import connection_string

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


def get_item(
        order: str, api_key: str = None, connection_pool=None, embedding_cache: redis.Redis = None,
        database_csv_file: StringIO = None
) -> str and bool:
    """

    @rtype: str + bool
    @param order: customers order ex. "Can I have a black coffee with 3 shots of cream."
    @param api_key: OpenAI auth
    @param connection_pool:
    @param embedding_cache: cache to reduce number of calls to OpenAI API
    @param database_csv_file: AWS RDS and PostgreSQL auth
    @return: Closest embedding along with a boolean flag to mark successful retrieval
    """
    if not order:
        return None, False

    return_queue = queue.Queue()

    def get_embedding() -> None:
        openai_embedding_time = time.time()
        if embedding_cache and embedding_cache.exists(order):
            logging.info("cache hit")
            vector_embedding = json.loads(embedding_cache.get(order))
        else:
            logging.info("cache miss")
            vector_embedding = openai_embedding_api(order, api_key if api_key else None)
            if embedding_cache:
                serialized_embedding = json.dumps(vector_embedding)
                embedding_cache.set(order, serialized_embedding)

        return_queue.put(vector_embedding)
        logging.info("openai_embedding time %s:", {time.time() - openai_embedding_time})

    get_embedding_thread = threading.Thread(target=get_embedding)
    get_embedding_thread.start()

    connection_time = time.time()
    if connection_pool:
        db_connection = connection_pool.getconn()
    else:
        db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    logging.info("db connection time %s:", time.time() - connection_time)

    set_session_time = time.time()
    db_connection.set_session(autocommit=True)
    logging.info("start new db session time %s:", {time.time() - set_session_time})

    def pg_register_vector() -> None:
        register_vector_time = time.time()
        register_vector(db_connection)
        logging.info("register_vector time %s:", {time.time() - register_vector_time})

    pg_register_vector_thread = threading.Thread(target=pg_register_vector)
    pg_register_vector_thread.start()

    cursor_time = time.time()
    cur = db_connection.cursor()
    logging.info("connecting cursor time %s:", {time.time() - cursor_time})

    get_embedding_thread.join()
    pg_register_vector_thread.join()

    try:
        embedding = return_queue.get(timeout=5)
    except queue.Empty:
        logging.info("queue empty")
        return "Error, return_queue.get turned into a deadlock. Check the `get_embedding` function", False

    execute_time = time.time()
    cur.execute(""" SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                    FROM products
                    ORDER BY embeddings <-> %s 
                    LIMIT 1;""",
                (np.array(embedding),))
    logging.info("execute query time %s:", {time.time() - execute_time})

    fetchall_time = time.time()
    result = cur.fetchall()
    logging.info("fetchall time %s:", {time.time() - fetchall_time})

    close_time = time.time()
    cur.close()
    logging.info("close cursor time %s:", {time.time() - close_time})

    close_connection_time = time.time()
    if connection_pool:
        connection_pool.putconn(db_connection)
    else:
        db_connection.close()
    logging.info("close db connection time %s:", {time.time() - close_connection_time})

    return result, True


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "openai_api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())

    get_secret()

    total_time = time.time()
    res = get_item(order="cappuccino", api_key=key, embedding_cache=None, connection_pool=connection_pool)
    print(f"total time: {time.time() - total_time}")

    print(res)

    return 0


if __name__ == "__main__":
    main()


'''
If ever change to hnsw index, use this code:
    cur.execute(f"""
                    SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                    FROM products
                    WHERE 1 - (embeddings <=> %s) > {0.8}
                    ORDER BY embeddings ASC
                    LIMIT 1;""",
                (np.array(embedding),))
'''