import time
import queue
import logging
import psycopg2
import threading
import numpy as np
from io import StringIO
from psycopg2 import pool
from pgvector.psycopg2 import register_vector
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.embeddings_api import *
from src.vector_db.aws_database_auth import connection_string

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


def get_item(order: str, api_key: str = None, connection_pool=None, database_csv_file: StringIO = None) -> str and bool:
    """

    @rtype: str + bool
    @param order: customers order ex. "Can I have a black coffee with 3 shots of cream."
    @param api_key: OpenAI auth
    @param connection_pool:
    @param database_csv_file: AWS RDS and PostgreSQL auth
    @return: Closest embedding along with a boolean flag to mark successful retrieval
    """
    if not order:
        return None, False

    connection_time = time.time()
    if connection_pool:
        db_connection = connection_pool.getconn()
    else:
        db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    logging.info(f"db connection time: {time.time() - connection_time}")

    set_session_time = time.time()
    db_connection.set_session(autocommit=True)
    logging.info(f"start new db session time: {time.time() - set_session_time}")

    return_queue = queue.Queue()

    def get_embedding() -> None:
        openai_embedding_time = time.time()
        vector_embedding = openai_embedding_api(order, api_key if api_key else None)
        logging.info(f"openai_embedding time: {time.time() - openai_embedding_time}")
        return_queue.put(vector_embedding)

    def pg_register_vector() -> None:
        register_vector_time = time.time()
        register_vector(db_connection)
        logging.info(f"register_vector time: {time.time() - register_vector_time}")

    get_embedding_thread = threading.Thread(target=get_embedding)
    pg_register_vector_thread = threading.Thread(target=pg_register_vector)

    get_embedding_thread.start()
    pg_register_vector_thread.start()

    cursor_time = time.time()
    cur = db_connection.cursor()
    logging.info(f"connecting cursor time: {time.time() - cursor_time}")

    get_embedding_thread.join()
    pg_register_vector_thread.join()

    execute_time = time.time()
    cur.execute(f""" SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                    FROM products
                    ORDER BY embeddings <-> %s 
                    LIMIT 1;""",
                (np.array(return_queue.get()),))
    logging.info(f"execute query time: {time.time() - execute_time}")

    fetchall_time = time.time()
    result = cur.fetchall()
    logging.info(f"fetchall time: {time.time() - fetchall_time}")

    close_time = time.time()
    cur.close()
    logging.info(f"close cursor time: {time.time() - close_time}")

    close_connection_time = time.time()
    if connection_pool:
        connection_pool.putconn(db_connection)
    else:
        db_connection.close()
    logging.info(f"close db connection time: {time.time() - close_connection_time}")

    return result, True


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())

    get_secret()

    total_time = time.time()
    res = get_item(order="cappuccino", api_key=key, connection_pool=connection_pool)
    logging.info(f"total time: {time.time() - total_time}")

    logging.info(res)

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