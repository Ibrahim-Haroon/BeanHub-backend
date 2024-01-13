import psycopg2
from io import StringIO
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.embeddings_api import *
from src.vector_db.aws_database_auth import connection_string


def add_item(item: dict, key: str = None, aws_csv_file: StringIO = None, database_csv_file: StringIO = None) -> bool:
    """

    @rtype: boolean
    @param item: new menu item to insert ex. {"MenuItem": {"itemName": "new_item", "item_quantity": "5", "common_allergin": "peanuts","num_calories": "250", "price": 1.25} }
    @param key: auth key for OpenAI
    @param aws_csv_file: SDK auth for AWS
    @param database_csv_file: auth to manager AWS RDS and PostgreSQL database
    @return: success if added into database else failure
    """
    if not item:
        return False

    get_secret(aws_csv_file if not None else None)
    db_connection = psycopg2.connect(connection_string(database_csv_file if not None else None))
    db_connection.set_session(autocommit=True)

    cur = db_connection.cursor()

    cur.execute("""
                INSERT INTO products (item_name, item_quantity, common_allergin, num_calories, price, embeddings)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (item["MenuItem"]["itemName"],
                  item["MenuItem"]["item_quantity"],
                  item["MenuItem"]["common_allergin"],
                  item["MenuItem"]["num_calories"],
                  item["MenuItem"]["price"],
                  openai_embedding_api(str(item), key if key else None)))

    cur.close()
    db_connection.close()

    return True


def main() -> int:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    item = {"MenuItem": {"itemName": "glaze_donut",
                         "item_quantity": "5",
                         "common_allergin": "peanuts",
                         "num_calories": "250",
                         "price": 1.25}
            }

    add_item(item=item, key=key)

    return 0


if __name__ == "__main__":
    main()