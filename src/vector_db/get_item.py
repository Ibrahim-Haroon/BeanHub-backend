import time
import queue
import psycopg2
import threading
import numpy as np
from io import StringIO
from psycopg2 import pool
from pgvector.psycopg2 import register_vector
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.openai_embeddings_api import *
from src.vector_db.aws_database_auth import connection_string


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
    print(f"connection time: {time.time() - connection_time}")

    set_session_time = time.time()
    db_connection.set_session(autocommit=True)
    print(f"set_session time: {time.time() - set_session_time}")

    return_queue = queue.Queue()

    def get_embedding() -> None:
        openai_embedding_time = time.time()
        vector_embedding = openai_embedding_api(order, api_key if api_key else None)
        print(f"openai_embedding time: {time.time() - openai_embedding_time}")
        return_queue.put(vector_embedding)

    def pg_register_vector() -> None:
        register_vector_time = time.time()
        register_vector(db_connection)
        print(f"register_vector time: {time.time() - register_vector_time}")

    get_embedding_thread = threading.Thread(target=get_embedding)
    pg_register_vector_thread = threading.Thread(target=pg_register_vector)

    get_embedding_thread.start()
    pg_register_vector_thread.start()

    get_embedding_thread.join()
    pg_register_vector_thread.join()

    cursor_time = time.time()
    cur = db_connection.cursor()
    print(f"cursor time: {time.time() - cursor_time}")

    # cur.execute(f"""
    #                 SELECT id, item_name, item_quantity, common_allergin, num_calories, price
    #                 FROM products
    #                 WHERE 1 - (embeddings <=> %s) > {0.8}
    #                 ORDER BY embeddings ASC
    #                 LIMIT 1;""",
    #             (np.array(embedding),))

    execute_time = time.time()
    cur.execute(f""" SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                    FROM products
                    ORDER BY embeddings <-> %s 
                    LIMIT 1;""",
                (np.array(return_queue.get()),))
    print(f"execute time: {time.time() - execute_time}")

    fetchall_time = time.time()
    result = cur.fetchall()
    print(f"fetchall time: {time.time() - fetchall_time}")

    close_time = time.time()
    cur.close()
    print(f"close time: {time.time() - close_time}")

    close_connection_time = time.time()
    if connection_pool:
        connection_pool.putconn(db_connection)
    else:
        db_connection.close()
    print(f"close_connection time: {time.time() - close_connection_time}")

    return result, True


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())

    get_secret()

    total_time = time.time()
    res = get_item(order="cappuccino", api_key=key, connection_pool=connection_pool)
    print(f"total time: {time.time() - total_time}")

    print(res)

    return 0


if __name__ == "__main__":
    main()