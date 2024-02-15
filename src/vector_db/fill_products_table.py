"""
This module contains the function fill_products_table which is used to
fill the products table in the database with menu csv file.
"""
from os import path
from io import StringIO
import psycopg2
from tqdm import tqdm
from pgvector.psycopg2 import register_vector
from other.red import input_red
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.embeddings_api import openai_embedding_api, parse_menu_csv
from src.vector_db.aws_database_auth import connection_string



def fill_products_table(
        data: list[dict], key: str = None,
        aws_csv_file: StringIO = None, database_csv_file: StringIO = None
) -> bool:
    """

    @rtype: bool
    @param data: all the menu items which have to be embedded and inserted in DB
    @param key: key for OpenAI auth
    @param aws_csv_file:  used for unit tests and if you want to pass in own AWS authentication
    @param database_csv_file: used for unit tests and
    if you want to pass in own database authentication
    @return: true if successfully created and filled table
    """

    if input_red() != "YES":
        return False

    if str(input("Enter the passkey to confirm: ")) != "beanKnowsWhatBeanWants":
        return False

    get_secret(aws_csv_file if not None else None)
    db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()

    cur.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'calorie_range') THEN
                CREATE TYPE calorie_range AS (
                    min int,
                    max int
                );
            END IF;
        END $$;
    """)


    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(db_connection)
    cur.execute("DROP TABLE IF EXISTS products;")

    cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                item_name text,
                item_quantity int,
                common_allergin text,
                num_calories calorie_range,
                price double precision,
                embeddings vector(1536)
            );
    """)

    for item in tqdm(data):
        num_calories = (int(item["MenuItem"]["num_calories"][0]),
                        int(item["MenuItem"]["num_calories"][1]))
        item_name = item["MenuItem"]["item_name"].lower()

        cur.execute("""
            INSERT INTO products (item_name, item_quantity, common_allergin, num_calories, price, embeddings)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (item_name,
              item["MenuItem"]["item_quantity"],
              item["MenuItem"]["common_allergin"].lower(),
              num_calories,
              item["MenuItem"]["price"],
              openai_embedding_api(item_name, key if key else None)))

    cur.execute("""
            CREATE INDEX ON products
            USING ivfflat (embeddings) 
            WITH (lists = 8);
    """)

    cur.execute("VACUUM ANALYZE products;")

    cur.close()
    db_connection.close()

    return True


def main(

) -> int:  # pragma: no cover
    """
    @rtype: int
    @return: 0 if successfully filled table
    """
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..",
                         "other", "openai_api_key.txt")
    with open(key_path, encoding='utf-8') as api_key:
        key = api_key.readline().strip()

    menu = parse_menu_csv()
    fill_products_table(menu, key)

    return 0


if __name__ == "__main__":  # pragma: no cover
    main()

# pylint: disable=W0105
'''
If ever want to use hnsw instead of ivfflat, use this code:
    cur.execute(f"""CREATE INDEX ON embeddings
                    USING hnsw(embedding vector_cosine_ops)
                    WITH (m=2, ef_construction=5);
    """)
'''