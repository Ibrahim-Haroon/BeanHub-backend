import psycopg2
from pgvector.psycopg2 import register_vector
from src.ai_integration.openai_embeddings_api import *
from src.vector_db.aws_sdk_auth import get_secret
from src.vector_db.aws_database_auth import connection_string
from other.red import inputRED
from io import StringIO


def fill_database(data: list[dict], key: str = None, aws_csv_file: StringIO = None, database_csv_file: StringIO = None) -> bool:
    """

    @rtype: bool
    @param data: all the menu items which have to be embedded and inserted in DB
    @param key: key for OpenAI auth
    @param aws_csv_file: can be passed if you want to pass in own AWS authentication and is used for unit tests
    @param database_csv_file: can be passed if you want to pass in own database authentication and is used for unit tests
    @return: true if successfully created and filled table
    """

    if (inputRED() != "YES"):
        return False
    else:
        if (str(input("Enter the passkey to confirm: ")) != "beanKnowsWhatBeanWants"):
            return False

    get_secret(aws_csv_file if not None else None)
    db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(db_connection)
    cur.execute("DROP TABLE IF EXISTS products;")

    cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                item_name text,
                item_quantity int,
                common_allergin text,
                num_calories, int,
                price double precision,
                embeddings vector(1536)
            );
        """)

    for item in data:
        cur.execute("""
            INSERT INTO products (item_name, item_quantity, common_allergin, num_calories, price, embeddings)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (item["MenuItem"]["itemName"],
              item["MenuItem"]["item_quantity"],
              item["MenuItem"]["common_allergin"],
              item["MenuItem"]["num_calories"],
              item["MenuItem"]["price"],
              openai_embedding_api(str(item), key)))

    cur.execute("""
            CREATE INDEX ON products
            USING ivfflat (embeddings) WITH (lists = 8);
        """)
    cur.execute("VACUUM ANALYZE products;")

    cur.close()
    db_connection.close()

    return True


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    menu = parse_menu_csv()
    fill_database(menu, key)

    return 0


if __name__ == "__main__":
    main()