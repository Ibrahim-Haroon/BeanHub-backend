"""
This module contains the function to check if an item is in stock and if the quantity is available.
"""
import json
from os import path
from io import StringIO
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.embeddings_api import openai_embedding_api
from src.vector_db.aws_database_auth import connection_string


def contains_quantity(
        order: str, quantity: int = 1, key: str = None,
        aws_csv_file: StringIO = None, database_csv_file: StringIO = None
) -> str:
    """
    This API is used to check if the item is in stock and if the quantity is available.
    @param order: customers order ex. "Can I have a black coffee with 3 shots of cream."
    @param quantity:
    @param key: auth key for OpenAI
    @param aws_csv_file: AWS SDK auth
    @param database_csv_file: AWS RDS and PostgreSQL auth
    @rtype: bool
    @return: Boolean flag to show whether the item is in stock
    """
    if not order:
        return json.dumps(False)

    get_secret(aws_csv_file if not None else None)
    db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()

    embedding = openai_embedding_api(order, key if key else None)
    register_vector(db_connection)

    cur.execute(""" SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                            FROM products
                            ORDER BY embeddings <-> %s limit 1;""",
                (np.array(embedding),))

    result = cur.fetchall()
    cur.close()
    db_connection.close()

    return json.dumps([result[0][2] >= quantity, result[0][2]])


def main(

) -> int:  # pragma: no cover
    """
    @rtype: int
    @return: 0 if successful
    """
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..",
                         "other", "openai_api_key.txt")
    with open(key_path, encoding='uft-8') as api_key:
        key = api_key.readline().strip()

    res = contains_quantity(order="cappuccino", quantity=7, key=key)

    print(bool(res))

    return 0


if __name__ == "__main__":  # pragma: no cover
    main()
