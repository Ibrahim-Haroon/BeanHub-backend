"""
script to parse menu and deals csv and get embeddings for menu items to be used by database queries
"""
import math
from os import path
from os import getenv as env
import pandas as pd
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings

load_dotenv()



def openai_embedding_api(
        text: str, api_key: str = None
) -> []:
    """
    This function takes in a menu item and returns the embeddings vector representation of the menu item
    @param text: str = menu item
    @param api_key: auth key for OpenAI
    @rtype: list[list[float]] (embeddings vector)
    @return: vector representation of menu item
    """
    if api_key:
        embeddings = OpenAIEmbeddings(api_key=api_key)
    else:
        embeddings = OpenAIEmbeddings(api_key=env('OPENAI_API_KEY'))

    return embeddings.embed_query(text)


def get_item_quantity(
        row: pd.Series
) -> int:
    """
    This function takes in a row from the pandas dataframe and returns the quantity of the item
    @param row: object from pandas dataframe
    @rtype: int
    @return: INT_MAX if item is a combo, else return the quantity
    """
    item_quantity = row
    if isinstance(item_quantity, float) and math.isnan(item_quantity):
        return 0x7fffffff

    return int(item_quantity)



def get_common_allergin(
        row: pd.Series
) -> str:
    """
    This function takes in a row from the pandas dataframe and returns the common allergin of the item
    @param row: object from pandas dataframe
    @rtype: str
    @return: "none" if item has no common allergin, else return the allergin
    """
    common_allergin = row
    if isinstance(common_allergin, float) and math.isnan(common_allergin):
        return "none"

    return str(common_allergin)


def get_calorie_range(
        row: pd.Series
) -> tuple[int, int]:
    """
    This function takes in a row from the pandas dataframe and returns the calorie range of the item
    @param row: object from pandas dataframe
    @rtype: tuple[int, int]
    @return: if object has set calories then tuple of min, min,
    else return tuple of min and max calories
    """
    calorie_range = row.split('-')
    min_cal = calorie_range[0]
    if len(calorie_range) == 1:
        return min_cal, min_cal

    max_cal = calorie_range[1]
    return min_cal, max_cal


def parse_menu_csv(

) -> list[dict]:
    """
    This function parses the menu.csv and returns a dictionary representation of the menu items
    @rtype: list[dict]
    @return: JSON object of menu items
    """
    menu_items = []

    menu_file_path = path.join(path.dirname(path.realpath(__file__)), "../IO", "menu.csv")

    df = pd.read_csv(menu_file_path)

    for _, row in df.iterrows():
        item_name = row['item_name']
        item_quantity = get_item_quantity(row['item_quantity'])
        common_allergin = get_common_allergin(row['common_allergin'])
        min_calories, max_calories = get_calorie_range(row['num_calories'])
        price = row['price']

        item = {
            "MenuItem": {
                "item_name": item_name,
                "item_quantity": item_quantity,
                "common_allergin": common_allergin,
                "num_calories": (min_calories, max_calories),
                "price": float(price)
            }
        }

        menu_items.append((item))

    return menu_items


def parse_deals_csv(

) -> list[dict]:
    """
    This function parses the deals.csv and returns a dictionary representation of the menu items
    @rtype: list[dict]
    @return: JSON object of menu items
    """
    deal_items = []

    deal_file_path = path.join(path.dirname(path.realpath(__file__)), "../IO", "deals.csv")

    df = pd.read_csv(deal_file_path)

    for _, row in df.iterrows():
        deal = row['deal']
        item_type: str = row['item_type']
        item_name: str = row['item_name']
        item_quantity: int = get_item_quantity(row['quantity'])
        price: int = row['price']
        related_items: float = row['related_items']

        item = {
            "Deal": {
                "deal": deal,
                "item_type": item_type,
                "item_name": item_name,
                "item_quantity": item_quantity,
                "price": float(price),
                "related_items": related_items
            }
        }

        deal_items.append((item))

    return deal_items


def main(
        key_path: str
) -> int:  # pragma: no cover
    """

    @param key_path: api key for OpenAI
    @return: 0 for success
    """
    with open(key_path, encoding='utf-8') as api_key:
        key = api_key.readline().strip()

    menu = parse_menu_csv()

    vectors = []

    for item in menu:
        vectors.append(openai_embedding_api(str(item), key))

    return 0


if __name__ == "__main__":  # pragma: no cover
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../..",
                              "other", "openai_api_key.txt")
    main(key_file_path)
