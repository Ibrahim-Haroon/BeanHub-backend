import psycopg2
import json
from io import StringIO
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.openai_embeddings_api import *
from src.vector_db.aws_database_auth import connection_string
from pgvector.psycopg2 import register_vector
import numpy as np


def contains_quantity(order: str, quantity: int = 1, aws_csv_file: StringIO = None, database_csv_file: StringIO = None):
    """

    @rtype: bool
    @param order: customers order ex. "Can I have a black coffee with 3 shots of cream."
    @param quantity:
    @param aws_csv_file: AWS SDK auth
    @param database_csv_file: AWS RDS and PostgreSQL auth
    @return: Boolean flag to show whether the item is in stock
    """
    if not order:
        return json.dumps(False)

    key = get_openai_key()
    get_secret(aws_csv_file if not None else None)
    db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()

    embedding = openai_embedding_api(order, key if key else None)
    register_vector(db_connection)

    cur.execute(f""" SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                            FROM products
                            ORDER BY embeddings <-> %s limit 1;""",
                (np.array(embedding),))

    result = cur.fetchall()
    cur.close()
    db_connection.close()

    return json.dumps([result[0][2] >= quantity, result[0][2]])


def get_openai_key(key_path: str = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key.txt")) -> str:
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    return key


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    res = contains_quantity(order="cappuccino", quantity=7, key=key)

    print(True if res else False)

    return 0


if __name__ == "__main__":
    main()

