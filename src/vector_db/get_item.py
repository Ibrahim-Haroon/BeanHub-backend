import psycopg2
import numpy as np
from io import StringIO
from psycopg2 import pool
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.openai_embeddings_api import *
from src.vector_db.aws_database_auth import connection_string
from pgvector.psycopg2 import register_vector


def get_item(order: str, api_key: str = None, connection_pool=None, aws_csv_file: StringIO = None, database_csv_file: StringIO = None) -> str and bool:
    """

    @rtype: str + bool
    @param order: customers order ex. "Can I have a black coffee with 3 shots of cream."
    @param api_key: OpenAI auth
    @param connection_pool:
    @param aws_csv_file: AWS SDK auth
    @param database_csv_file: AWS RDS and PostgreSQL auth
    @return: Closest embedding along with a boolean flag to mark successful retrieval
    """
    if not order:
        return None, False

    get_secret(aws_csv_file if not None else None)
    if connection_pool:
        db_connection = connection_pool.getconn()
    else:
        db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()

    embedding = openai_embedding_api(order, api_key if api_key else None)
    register_vector(db_connection)

    # cur.execute(f"""
    #                 SELECT id, item_name, item_quantity, common_allergin, num_calories, price
    #                 FROM products
    #                 WHERE 1 - (embeddings <=> %s) > {0.8}
    #                 ORDER BY embeddings ASC
    #                 LIMIT 1;""",
    #             (np.array(embedding),))


    cur.execute(f""" SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                    FROM products
                    ORDER BY embeddings <-> %s 
                    LIMIT 1;""",
                (np.array(embedding),))

    result = cur.fetchall()

    cur.close()
    if connection_pool:
        connection_pool.putconn(db_connection)
    else:
        db_connection.close()

    return result, True


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())

    res = get_item(order="cappuccino", api_key=key, connection_pool=connection_pool)

    print(res)

    return 0


if __name__ == "__main__":
    main()
