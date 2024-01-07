from langchain.embeddings import OpenAIEmbeddings
from os import path
import pandas as pd
import math


def openai_embedding_api(text: str, api_key: str = None) -> []:
    """

    @rtype: list[list[float]] (embeddings vector)
    @param text: str = menu item
    @param api_key: auth key for OpenAI
    @return: vector of menu item
    """

    embeddings = OpenAIEmbeddings(api_key=api_key)

    return embeddings.embed_query(text)


def get_item_quantity(row: pd.Series) -> int:
    """

    @rtype: int
    @param row: object from pandas dataframe
    @return: INT_MAX if item is a combo, else return the quantity
    """
    item_quantity = row
    if isinstance(item_quantity, float) and math.isnan(item_quantity):
        return 0x7fffffff
    else:
        return int(item_quantity)



def get_common_allergin(row: pd.Series) -> str:
    """

    @rtype: str
    @param row: object from pandas dataframe
    @return: "none" if item has no common allergin, else return the allergin
    """
    common_allergin = row
    if isinstance(common_allergin, float) and math.isnan(common_allergin):
        return "none"
    else:
        return str(common_allergin)


def get_calorie_range(row: pd.Series) -> tuple[int, int]:
    """

    @rtype: tuple[int, int]
    @param row: object from pandas dataframe
    @return: if object has set calories then tuple of min, min, else return tuple of min and max calories
    """
    calorie_range = row.split('-')
    min_cal = calorie_range[0]
    if len(calorie_range) == 1:
        return min_cal, min_cal
    else:
        max_cal = calorie_range[1]
        return min_cal, max_cal


def parse_menu_csv() -> list[dict]:
    """

    @rtype: list[dict]
    @return: JSON object of menu items
    """
    menu_items = []

    menu_file_path = path.join(path.dirname(path.realpath(__file__)), "../IO", "menu.csv")

    df = pd.read_csv(menu_file_path)

    for index, row in df.iterrows():
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


def main(key_path: str) -> int:
    """

    @param key_path: api key for OpenAI
    @return: 0 for success
    """
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    menu = parse_menu_csv()

    # print(menu)

    vectors = []

    for item in menu:
        # vectors.append(openai_embedding_api(str(item), key))
        num_calories = (int(item["MenuItem"]["num_calories"][0]), int(item["MenuItem"]["num_calories"][1]))
        # print(type(item["MenuItem"]["num_calories"][0]))
        print(num_calories)

    return 0


if __name__ == "__main__":
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key.txt")
    main(key_file_path)