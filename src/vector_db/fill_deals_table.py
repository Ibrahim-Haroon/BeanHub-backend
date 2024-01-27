import psycopg2
from os import path
from tqdm import tqdm
from io import StringIO
from other.red import inputRED
from pgvector.psycopg2 import register_vector
from src.vector_db.aws_sdk_auth import get_secret
from src.vector_db.aws_database_auth import connection_string
from src.ai_integration.embeddings_api import parse_deals_csv, openai_embedding_api


def fill_deals_table(
        deals: list[dict], key: str = None,
        aws_csv_file: StringIO = None, database_csv_file: StringIO = None
) -> bool:
    """

    @rtype: bool
    @param deals: all the menu items which have to be embedded and inserted in DB
    @param key: key for OpenAI auth
    @param aws_csv_file:  used for unit tests and if you want to pass in own AWS authentication
    @param database_csv_file: used for unit tests and if you want to pass in own database authentication
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
    cur.execute("DROP TABLE IF EXISTS deals;")

    cur.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id SERIAL PRIMARY KEY,
                deal text,
                item_type text,
                item_name text,
                item_quantity int,
                price double precision,
                related_items text,
                embeddings vector(1536)
            );
    """)

    for item in tqdm(deals):
        deal = item["Deal"]["deal"].lower()
        item_name = item["Deal"]["item_name"].lower()
        related_items = item["Deal"]["related_items"].lower()

        cur.execute("""
            INSERT INTO deals (deal, item_type, item_name, item_quantity, price, related_items, embeddings)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (deal,
              item["Deal"]["item_type"],
              item_name,
              item["Deal"]["item_quantity"],
              item["Deal"]["price"],
              related_items,
              openai_embedding_api(related_items, key if key else None)))

    cur.execute("""
            CREATE INDEX ON deals
            USING ivfflat (embeddings) 
            WITH (lists = 8);
    """)

    cur.execute("VACUUM ANALYZE deals;")

    cur.close()
    db_connection.close()

    return True


def main(

) -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "openai_api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    deals = parse_deals_csv()
    fill_deals_table(deals, key)

    return 0


if __name__ == "__main__":
    main()

'''
If ever want to use hnsw instead of ivfflat, use this code:
    cur.execute(f"""CREATE INDEX ON deals
                    USING hnsw(embedding vector_cosine_ops)
                    WITH (m=2, ef_construction=5);
    """)
'''
