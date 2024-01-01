import psycopg2
from io import StringIO
from scripts.server.vector_db.aws_secret import get_secret
from scripts.ai_integration.openai_embeddings_api import *
from scripts.server.vector_db.connection_string import connection_string
from scripts.ai_integration.nlp_bert import ner_transformer
import numpy as np


def similarity_search(order: str, top_k: int = 3, key: str = None, aws_csv_file: StringIO = None, database_csv_file: StringIO = None) -> object:
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
    embedding = openai_embedding_api(str(formatted_thing), key)

    get_secret(aws_csv_file if not None else None)
    db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()
    cur.execute(f""" SELECTED id, item_name, item_quantity, common_allergin, num_calories, price, embeddings
                    FROM products
                    ORDER BY embeddings <-> %s limit {top_k};""",
                (np.array(embedding),))
    results = cur.fetchall()

    cur.close()
    db_connection.close()

    return results, True


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    similarity_search(order="dummy", key=key)

    return 0


if __name__ == "__main__":
    main()
