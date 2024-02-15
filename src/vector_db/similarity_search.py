"""
This module contains the function `similarity_search` which is used to search
for the most similar embeddings to a given order. Currently unused.
"""
from os import path
from io import StringIO
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.embeddings_api import openai_embedding_api
from src.vector_db.aws_database_auth import connection_string
from src.ai_integration.fine_tuned_nlp import ner_transformer


def similarity_search(
        order: str, top_k: int = 3, key: str = None,
        aws_csv_file: StringIO = None, database_csv_file: StringIO = None
) -> list and bool:
    """

    @rtype: list[list[float]] + boolean
    @param order: customers order ex. "Can I have a black coffee with 3 shots of cream."
    @param top_k: The number of closest embeddings you want
    @param key: OpenAI auth
    @param aws_csv_file: AWS SDK auth
    @param database_csv_file: AWS RDS and PostgreSQL auth
    @return: the list of 3 closest embeddings along with a boolean flag to mark success
    """
    if not order:
        return None, False

    formatted_thing = ner_transformer(order)

    get_secret(aws_csv_file if not None else None)
    db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()

    embedding = openai_embedding_api(str(formatted_thing), key if key else None)
    register_vector(db_connection)

    cur.execute(f""" SELECT id, item_name, item_quantity, common_allergin, num_calories, price
                        FROM products
                        ORDER BY embeddings <-> %s limit {top_k};""",
                (np.array(embedding),))

    results = cur.fetchall()

    cur.close()
    db_connection.close()

    return results, True


def main(

) -> int:  # pragma: no cover
    """
    @rtype: int
    @return: 0 if successful
    """
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..",
                         "other", "openai_api_key.txt")
    with open(key_path, encoding='utf-8') as api_key:
        key = api_key.readline().strip()

    similarity_search(order="dummy", key=key)

    return 0


if __name__ == "__main__":  # pragma: no cover
    main()
