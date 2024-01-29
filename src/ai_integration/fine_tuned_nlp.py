import re
import time
import logging
import threading
from os import path
import psycopg2.pool
from redis import Redis
from os import getenv as env
from dotenv import load_dotenv
from other.regex_patterns import *
from other.number_map import number_map
from src.vector_db.get_item import get_item
from simpletransformers.ner import NERModel
from src.django_beanhub.settings import DEBUG
from src.vector_db.aws_sdk_auth import get_secret
from src.vector_db.aws_database_auth import connection_string

logging_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


def ner_transformer(
        input_string: str = None,
        print_prediction: bool = False
) -> list:
    """

    @rtype: list of dictionaries
    @param input_string: customer request ex. "I want a black coffee"
    @param print_prediction: boolean flag to print predictions
    @return: predictions generated from fine-tuned transformer
    """
    if not input_string or not isinstance(input_string, str):
        return []

    transformer_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other/genai_models/")

    model = NERModel('bert', transformer_file_path, use_cuda=False)

    prediction, _ = model.predict([input_string])

    if print_prediction:
        print(prediction)

    return prediction


class Order:
    def __init__(
            self, formatted_order: str, connection_pool=None,
            embedding_cache: Redis = None, aws_connected: bool = False
    ):  # pragma: no cover
        init_time = time.time()
        self.__order: str = formatted_order.casefold().strip()
        self.__allergies: str = ""
        self.__item_name: str = ""
        self.__quantity: list[int] = []
        self.__price: list[float] = []
        self.__temp: str = ""
        self.__add_ons: list[str] = []
        self.__milk_type: str = ""
        self.__sweeteners: list[str] = []
        self.__num_calories: list[str] = []
        self.__cart_action: str = ""
        self.__size: str = ""
        if embedding_cache:
            self.__embedding_cache = embedding_cache
        else:
            self.__embedding_cache = None
        key_path = path.join(path.dirname(path.realpath(__file__)),
                             "../../other/" + "openai_api_key.txt")
        if path.exists(key_path):
            with open(key_path) as KEY:
                self.__key = KEY.readline().strip()
        else:
            self.__key = env('OPENAI_API_KEY')
        if connection_pool:
            self.connection_pool = connection_pool
        else:
            logging.debug("creating new connection pool")
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(1,
                                                                      10,
                                                                      connection_string())

        if not aws_connected:
            logging.debug("getting aws secret")
            get_secret()
        logging.debug(f"initialising order time: {time.time() - init_time}")

    def make_order(
            self
    ) -> dict:
        order_type, order_details = self.__get_order_type()

        if order_type == "coffee":
            return self.__make_coffee_order(order_details)
        elif order_type == "beverage":
            return self.__make_beverage_order(order_details)
        elif order_type == "food":
            return self.__make_food_order(order_details)
        elif order_type == "bakery":
            return self.__make_bakery_order(order_details)

        return {}

    def __get_order_type(
            self
    ) -> tuple[str, dict]:  # pragma: no cover
        order_details = self.__parse_order()

        if order_details['coffee']:
            return "coffee", order_details
        elif order_details['beverage']:
            return "beverage", order_details
        elif order_details['food']:
            return "food", order_details
        elif order_details['bakery']:
            return "bakery", order_details

        return "", {}

    def __make_coffee_order(
            self, order_details
    ) -> dict:  # pragma: no cover
        self.__cart_action = self.__get_cart_action()
        self.__item_name = order_details['coffee'][0]
        self.__calculate_quantity(order_details['quantities'])
        self.__temp = "regular" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.__sweeteners.extend(order_details['sweeteners'])
        self.__add_ons.extend(order_details['add_ons'])
        self.__milk_type = "regular" if not order_details['milk_type'] else str(order_details['milk_type'][0])
        self.__size = "regular" if not order_details['sizes'] else str(order_details['sizes'][0])
        self.__get_price_and_allergies_and_num_calories()
        return {
            "CoffeeItem": {
                "item_name": self.__item_name,
                "quantity": self.__quantity,
                "price": self.__price,
                "temp": self.__temp,
                "add_ons": self.__add_ons,
                "milk_type": self.__milk_type,
                "sweeteners": self.__sweeteners,
                "num_calories": self.__num_calories,
                "size": self.__size,
                "cart_action": self.__cart_action,
                "common_allergies_in_item": self.__allergies
            }
        }

    def __make_beverage_order(
            self, order_details
    ) -> dict:  # pragma: no cover
        self.__cart_action = self.__get_cart_action()
        self.__item_name = order_details['beverage'][0]
        self.__calculate_quantity(order_details['quantities'])
        self.__temp = "regular" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.__sweeteners = order_details['sweeteners']
        self.__add_ons = order_details['add_ons']
        self.__size = "regular" if not order_details['sizes'] else str(order_details['sizes'][0])
        self.__get_price_and_allergies_and_num_calories()
        return {
            "BeverageItem": {
                "item_name": self.__item_name,
                "quantity": self.__quantity,
                "price": self.__price,
                "temp": self.__temp,
                "add_ons": self.__add_ons,
                "sweeteners": self.__sweeteners,
                "num_calories": self.__num_calories,
                "size": self.__size,
                "cart_action": self.__cart_action,
                "common_allergies_in_item": self.__allergies
            }
        }

    def __make_food_order(
            self,
            order_details
    ) -> dict:  # pragma: no cover
        self.__cart_action = self.__get_cart_action()
        self.__item_name = order_details['food'][0]
        self.__calculate_quantity(order_details['quantities'])
        self.__get_price_and_allergies_and_num_calories()
        return {
            "FoodItem": {
                "item_name": self.__item_name,
                "quantity": self.__quantity,
                "price": self.__price,
                "num_calories": self.__num_calories,
                "cart_action": self.__cart_action,
                "common_allergies_in_item": self.__allergies
            }
        }

    def __make_bakery_order(
            self,
            order_details
    ) -> dict:  # pragma: no cover
        self.__cart_action = self.__get_cart_action()
        self.__item_name = order_details['bakery'][0]
        self.__calculate_quantity(order_details['quantities'])
        self.__get_price_and_allergies_and_num_calories()
        return {
            "BakeryItem": {
                "item_name": self.__item_name,
                "quantity": self.__quantity,
                "price": self.__price,
                "num_calories": self.__num_calories,
                "cart_action": self.__cart_action,
                "common_allergies_in_item": self.__allergies
            }
        }

    def __calculate_quantity(
            self,
            quantities
    ) -> None:  # pragma: no cover
        for quantity in quantities:
            try:
                quantity = int(quantity)
            except ValueError:
                quantity = number_map(quantity)
            if self.__cart_action == "modification":
                self.__quantity.append(-1 * quantity)
            else:
                self.__quantity.append(quantity)

        return

    def __get_cart_action(
            self
    ) -> str:  # pragma: no cover
        if self.__is_question():
            return "question"
        elif self.__is_modification():
            return "modification"
        else:
            return "insertion"

    def __is_question(
            self
    ) -> bool:  # pragma: no cover
        pattern = r'\b(do you|how many|how much|does|what are)\b'

        return bool(re.search(pattern, self.__order))

    def __is_modification(
            self
    ) -> bool:  # pragma: no cover
        pattern = (r'\b(actually remove|actually change|dont want|don\'t want|remove|change|swap|adjust|modify|take '
                   r'away|replace)\b')

        return bool(re.search(pattern, self.__order))

    def __get_price_and_allergies_and_num_calories(
            self
    ) -> None:  # pragma: no cover
        db_time = time.time()

        item_thread = threading.Thread(target=self.__process_item_and_allergies)
        add_ons_thread = threading.Thread(target=self.__process_add_ons)
        sweeteners_thread = threading.Thread(target=self.__process_sweeteners)
        milk_thread = threading.Thread(target=self.__process_milk)

        item_thread.start()
        add_ons_thread.start()
        sweeteners_thread.start()
        milk_thread.start()

        item_thread.join()
        add_ons_thread.join()
        sweeteners_thread.join()
        milk_thread.join()

        logging.debug(f"querying db for price, allergies, and num of calories time: {time.time() - db_time}")
        return

    def __process_item_and_allergies(
            self
    ) -> None:  # pragma: no cover
        item_details, _ = get_item(self.__item_name,
                                   connection_pool=self.connection_pool,
                                   embedding_cache=self.__embedding_cache if self.__embedding_cache else None,
                                   api_key=self.__key)

        if self.__cart_action == "question":
            self.__quantity.append(item_details[0][2])

        self.__allergies = item_details[0][3]
        self.__price.append(item_details[0][5])
        self.__num_calories.append(item_details[0][4])

    def __process_add_ons(
            self
    ) -> None:  # pragma: no cover
        for add_on in self.__add_ons:
            add_on_details, _ = get_item(add_on,
                                         connection_pool=self.connection_pool,
                                         embedding_cache=self.__embedding_cache if self.__embedding_cache else None,
                                         api_key=self.__key)
            self.__price.append(add_on_details[0][5])
            self.__num_calories.append(add_on_details[0][4])
            if self.__cart_action == "question":
                self.__quantity.append(add_on_details[0][2])

    def __process_sweeteners(
            self
    ) -> None:  # pragma: no cover
        for sweetener in self.__sweeteners:
            sweetener_details, _ = get_item(sweetener,
                                            connection_pool=self.connection_pool,
                                            embedding_cache=self.__embedding_cache if self.__embedding_cache else None,
                                            api_key=self.__key)
            self.__price.append(sweetener_details[0][5])
            self.__num_calories.append(sweetener_details[0][4])
            if self.__cart_action == "question":
                self.__quantity.append(sweetener_details[0][2])

    def __process_milk(
            self
    ) -> None:  # pragma: no cover
        if self.__milk_type and self.__milk_type != "regular":
            milk_details, _ = get_item(self.__milk_type,
                                       connection_pool=self.connection_pool,
                                       embedding_cache=self.__embedding_cache if self.__embedding_cache else None,
                                       api_key=self.__key)
            self.__price.append(milk_details[0][5])
            self.__num_calories.append(milk_details[0][4])
            if self.__cart_action == "question":
                self.__quantity.append(milk_details[0][2])

    def __parse_order(
            self
    ) -> dict:  # pragma: no cover
        sizes = re.findall(size_pattern, self.__order)
        quantities = re.findall(quantity_pattern, self.__order)
        coffees = re.findall(coffee_pattern, self.__order)
        temperatures = re.findall(temperature_pattern, self.__order)
        sweeteners = re.findall(sweetener_pattern, self.__order)
        flavors = re.findall(flavor_pattern, self.__order)
        beverages = re.findall(beverage_pattern, self.__order)
        foods = re.findall(food_pattern, self.__order)
        bakeries = re.findall(bakery_pattern, self.__order)
        add_ons = re.findall(add_ons_pattern, self.__order)
        milk_types = re.findall(milk_pattern, self.__order)
        allergies = re.findall(common_allergies, self.__order)

        return {
            "sizes": sizes,
            "quantities": quantities,
            "coffee": coffees,
            "temperature": temperatures,
            "sweeteners": sweeteners,
            "flavors": flavors,
            "beverage": beverages,
            "food": foods,
            "bakery": bakeries,
            "add_ons": add_ons,
            "milk_type": milk_types,
            "allergies": allergies
        }


def split_order(
        order
) -> list[str]:
    start_time = time.time()
    split = re.split(split_pattern, order)
    remove_words = ['plus', 'get', 'and', 'also']
    remove_chars = '[^a-zA-Z0-9]'

    filtered_order = [order for order in split if order not in remove_words and order != remove_chars and order]

    logging.debug(f"split order time: {time.time() - start_time}")
    return filtered_order


def make_order_report(
        split_orders: list[str], connection_pool=None, embedding_cache: Redis = None,
        aws_connected: bool = False
) -> [list[dict]] and str:
    start_time = time.time()
    order_report, model_report = [], []

    threads = []
    for order in split_orders:
        order_thread = threading.Thread(target=process_order, args=(order,
                                                                    order_report,
                                                                    model_report,
                                                                    connection_pool,
                                                                    embedding_cache,
                                                                    aws_connected))
        threads.append(order_thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    logging.debug(f"make order report time: {time.time() - start_time}")

    return order_report, ''.join(model_report)


def process_order(
        order, order_report, model_report, connection_pool,
        embedding_cache, aws_connected
) -> None:
    item_types = ['CoffeeItem', 'BeverageItem', 'FoodItem', 'BakeryItem']
    final_order = ((Order(order, connection_pool, embedding_cache, aws_connected).make_order()))

    if final_order:
        model_report.append(str(final_order))
        for item_type in item_types:
            if item_type in final_order:
                final_order[item_type].pop('common_allergies_in_item')
                break
        order_report.append(final_order)


def human_requested(
        transcription: str
) -> bool:
    transcription = transcription.lower()
    pattern = r'\b(human|person|employee|worker|staff member|manager|owner|workman|hired help|crew member|agent)\b'
    return bool(re.search(pattern, transcription))


def accepted_deal(
        transcription: str
) -> bool:  # pragma: no cover
    transcription = transcription.lower()
    pattern = r'\b(yes|yeah|sure|okay|ok|yup|yep|alright|fine|deal|k)\b'
    return bool(re.search(pattern, transcription))


if __name__ == "__main__":  # pragma: no cover
    total_time = time.time()

    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "openai_api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    orders = "2 coffees with two pumps of vanilla and one pump of caramel and two splenda packets"

    split_order_time = time.time()
    details = split_order(orders)
    print(f"Split order time: {time.time() - split_order_time} seconds")
    print(details)

    make_order_report_time = time.time()
    report, model_version = make_order_report(details)
    print(f"Make order report time: {time.time() - make_order_report_time} seconds")

    print(report)

    end_time = time.time()
    execution_time = end_time - total_time
    print(f"Execution time: {execution_time} seconds")
