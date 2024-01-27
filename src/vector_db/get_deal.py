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
from src.django_beanhub.settings import DEBUG
from pgvector.psycopg2 import register_vector
from src.vector_db.aws_sdk_auth import get_secret
from src.vector_db.aws_database_auth import connection_string
from src.ai_integration.embeddings_api import openai_embedding_api

logging_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s:%(levelname)s:%(message)s')


def get_deal(
        order: dict, api_key: str = None, connection_pool=None, embedding_cache: redis.Redis = None,
        database_csv_file: StringIO = None
) -> str and dict and bool:
    """

    @rtype: str + dict + bool
    @param order: order_report from fine_tuned_nlp.py
    @param api_key: OpenAI auth
    @param connection_pool:
    @param embedding_cache: cache to reduce number of calls to OpenAI API
    @param database_csv_file: AWS RDS and PostgreSQL auth
    @return: Closest embedding along, object that can be used by frontend, a boolean flag to mark successful retrieval
    """
    if not order:
        return None, None, False

    return_queue = queue.Queue()

    item_types = ['CoffeeItem', 'BeverageItem', 'FoodItem', 'BakeryItem']
    product_name = None

    for item_type in item_types:
        if order.get(item_type) and order[item_type]['cart_action'] != 'question':
            product_name = order[item_type]['item_name']
            break

    if not product_name:
        return None, None, False

    def get_embedding() -> None:
        openai_embedding_time = time.time()
        if embedding_cache and embedding_cache.exists(product_name):
            logging.debug("cache hit")
            vector_embedding = json.loads(embedding_cache.get(product_name))
        else:
            logging.debug("cache miss")
            vector_embedding = openai_embedding_api(product_name, api_key if api_key else None)
            if embedding_cache:
                serialized_embedding = json.dumps(vector_embedding)
                embedding_cache.set(product_name, serialized_embedding)

        return_queue.put(vector_embedding)
        logging.debug("openai_embedding time %s:", {time.time() - openai_embedding_time})

    get_embedding_thread = threading.Thread(target=get_embedding)
    get_embedding_thread.start()

    connection_time = time.time()
    if connection_pool:
        db_connection = connection_pool.getconn()
    else:
        db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    logging.debug("db connection time %s:", time.time() - connection_time)

    set_session_time = time.time()
    db_connection.set_session(autocommit=True)
    logging.debug("start new db session time %s:", {time.time() - set_session_time})

    def pg_register_vector() -> None:
        register_vector_time = time.time()
        register_vector(db_connection)
        logging.debug("register_vector time %s:", {time.time() - register_vector_time})

    pg_register_vector_thread = threading.Thread(target=pg_register_vector)
    pg_register_vector_thread.start()

    cursor_time = time.time()
    cur = db_connection.cursor()
    logging.debug("connecting cursor time %s:", {time.time() - cursor_time})

    get_embedding_thread.join()
    pg_register_vector_thread.join()

    try:
        embedding = return_queue.get(timeout=5)
    except queue.Empty:
        logging.debug("queue empty")
        return "Error, return_queue.get turned into a deadlock. Check the `get_embedding` function", False

    execute_time = time.time()
    cur.execute(""" SELECT deal, item_type, item_name, item_quantity, price
                    FROM deals
                    ORDER BY embeddings <-> %s 
                    LIMIT 1;""",
                (np.array(embedding),))
    logging.debug("execute query time %s:", {time.time() - execute_time})

    fetchall_time = time.time()
    result = cur.fetchall()
    logging.debug("fetchall time %s:", {time.time() - fetchall_time})

    close_time = time.time()
    cur.close()
    logging.debug("close cursor time %s:", {time.time() - close_time})

    close_connection_time = time.time()
    if connection_pool:
        connection_pool.putconn(db_connection)
    else:
        db_connection.close()
    logging.debug("close db connection time %s:", {time.time() - close_connection_time})

    deal = result[0][0]
    item_type: str = result[0][1]
    item_name: str = result[0][2]
    # item_quantity: int = result[0][3]
    item_price = (result[0][4])

    deal_object = {
        item_type: {
            "item_name": item_name,
            "quantity": [1],
            "price": [item_price],
            "cart_action": "insertion"
        }
    }

    return deal, deal_object, True


def main(

) -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "openai_api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    order = {
        "CoffeeItem": {
            "item_name": "glazed donut",
            "cart_action": "insertion"
        }
    }
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())

    get_secret()

    total_time = time.time()
    res = get_deal(order=order, api_key=key, embedding_cache=None, connection_pool=connection_pool)
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