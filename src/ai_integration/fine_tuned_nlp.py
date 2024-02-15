"""
script for taking in customer order and parsing it to make usable data for the computations
"""
import re  # pylint: disable=W0614
import time
import logging
import threading
from os import path
from os import getenv as env
from dotenv import load_dotenv
import psycopg2.pool
from redis import Redis
from simpletransformers.ner import NERModel
from other.regex_patterns import *  # pylint: disable=W0401,W0614
from other.quantity_correction import *  # pylint: disable=W0401,W0614
from other.number_map import number_map
from src.vector_db.get_item import get_item
from src.django_beanhub.settings import DEBUG
from src.vector_db.aws_sdk_auth import get_secret
from src.vector_db.aws_database_auth import connection_string

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')

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

    transformer_file_path = path.join(path.dirname(path.realpath(__file__)), "../..",
                                      "other/genai_models/")

    model = NERModel('bert', transformer_file_path, use_cuda=False)

    prediction, _ = model.predict([input_string])

    if print_prediction:
        print(prediction)

    return prediction


# pylint: disable=R0902, R0903
class Order:
    """
    class to process the order and make a report
    """

    def __init__(
            self, formatted_order: str, connection_pool=None,
            embedding_cache: Redis = None, aws_connected: bool = False
    ):
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
            with open(key_path, encoding='utf-8') as _key_:
                self.__key = _key_.readline().strip()
        else:
            self.__key = env('OPENAI_API_KEY')
        if connection_pool:
            self.__connection_pool = connection_pool
        else:
            logging.debug("creating new connection pool")
            self.__connection_pool = psycopg2.pool.SimpleConnectionPool(1,
                                                                        10,
                                                                        connection_string())

        if not aws_connected:
            logging.debug("getting aws secret")
            get_secret()
        logging.debug("initialising order time: %s", (time.time() - init_time))

    def make_order(
            self
    ) -> dict:
        """
        @rtype: dict
        @return: dictionary object of the order
        """
        order_type, order_details = self.__get_order_type()
        self.__verify_quantities(order_type, order_details)

        if order_type == "coffee":
            return self.__make_coffee_order(order_details)
        if order_type == "beverage":
            return self.__make_beverage_order(order_details)
        if order_type == "food":
            return self.__make_food_order(order_details)
        if order_type == "bakery":
            return self.__make_bakery_order(order_details)

        return {}

    def __get_order_type(
            self
    ) -> tuple[str, dict]:
        order_details = self.__parse_order()

        if order_details['coffee']:
            return "coffee", order_details
        if order_details['beverage']:
            return "beverage", order_details
        if order_details['food']:
            return "food", order_details
        if order_details['bakery']:
            return "bakery", order_details

        return "", {}

    def __make_coffee_order(
            self, order_details
    ) -> dict:
        self.__cart_action = self.__get_cart_action()
        self.__item_name = order_details['coffee'][0]
        self.__calculate_quantity(order_details['quantities'])
        self.__temp = "regular" \
            if not order_details['temperature'] \
            else str(order_details['temperature'][0])
        self.__sweeteners.extend(order_details['sweeteners'])
        self.__add_ons.extend(order_details['add_ons'])
        self.__milk_type = "regular" \
            if not order_details['milk_type'] \
            else str(order_details['milk_type'][0])
        self.__size = "regular" \
            if not order_details['sizes'] \
            else str(order_details['sizes'][0])
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
    ) -> dict:
        self.__cart_action = self.__get_cart_action()
        self.__item_name = order_details['beverage'][0]
        self.__calculate_quantity(order_details['quantities'])
        self.__temp = "regular" \
            if not order_details['temperature'] \
            else str(order_details['temperature'][0])
        self.__sweeteners = order_details['sweeteners']
        self.__add_ons = order_details['add_ons']
        self.__size = "regular" \
            if not order_details['sizes'] \
            else str(order_details['sizes'][0])
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
    ) -> dict:
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
    ) -> dict:
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
    ) -> None:
        for quantity in quantities:
            if quantity.isnumeric():
                quantity = int(quantity)
            else:
                quantity = number_map(quantity)
            if self.__cart_action == "modification":
                self.__quantity.append(-1 * quantity)
            else:
                self.__quantity.append(quantity)

    def __get_cart_action(
            self
    ) -> str:
        if self.__is_question():
            return "question"
        if self.__is_modification():
            return "modification"

        return "insertion"

    def __is_question(
            self
    ) -> bool:
        pattern = r'\b(do you|how many|how much|does|what are)\b'

        return bool(re.search(pattern, self.__order))

    def __is_modification(
            self
    ) -> bool:
        pattern = (r'\b(actually remove|actually change|dont want|don\'t want|'
                   r'remove|change|swap|adjust|modify|take|away|replace|minus|deduct)\b')

        return bool(re.search(pattern, self.__order))

    def __get_price_and_allergies_and_num_calories(
            self
    ) -> None:
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

        logging.debug("querying db for price, allergies, and num of calories time: %s",
                      time.time() - db_time)

    def __process_item_and_allergies(
            self
    ) -> None:
        item_details, _ = get_item(self.__item_name,
                                   connection_pool=self.__connection_pool,
                                   embedding_cache=self.__embedding_cache
                                   if self.__embedding_cache else None,
                                   api_key=self.__key)

        if self.__cart_action == "question":
            self.__quantity = []
            self.__quantity.append(item_details[0][2])

        self.__allergies = item_details[0][3]
        self.__price.append(item_details[0][5])
        self.__num_calories.append(item_details[0][4])

    def __process_add_ons(
            self
    ) -> None:
        for add_on in self.__add_ons:
            add_on_details, _ = get_item(add_on,
                                         connection_pool=self.__connection_pool,
                                         embedding_cache=self.__embedding_cache
                                         if self.__embedding_cache
                                         else None,
                                         api_key=self.__key)
            self.__price.append(add_on_details[0][5])
            self.__num_calories.append(add_on_details[0][4])
            if self.__cart_action == "question":
                self.__quantity.append(add_on_details[0][2])

    def __process_sweeteners(
            self
    ) -> None:
        for sweetener in self.__sweeteners:
            sweetener_details, _ = get_item(sweetener,
                                            connection_pool=self.__connection_pool,
                                            embedding_cache=self.__embedding_cache
                                            if self.__embedding_cache
                                            else None,
                                            api_key=self.__key)
            self.__price.append(sweetener_details[0][5])
            self.__num_calories.append(sweetener_details[0][4])
            if self.__cart_action == "question":
                self.__quantity.append(sweetener_details[0][2])

    def __process_milk(
            self
    ) -> None:
        if self.__milk_type and self.__milk_type != "regular":
            milk_details, _ = get_item(self.__milk_type,
                                       connection_pool=self.__connection_pool,
                                       embedding_cache=self.__embedding_cache
                                       if self.__embedding_cache
                                       else None,
                                       api_key=self.__key)
            self.__price.append(milk_details[0][5])
            self.__num_calories.append(milk_details[0][4])
            if self.__cart_action == "question":
                self.__quantity.append(milk_details[0][2])

    def __parse_order(
            self
    ) -> dict:
        sizes = [match for match in re.findall(SIZE_PATTERN, self.__order) if match]
        quantities = [match for match in re.findall(QUANTITY_PATTERN, self.__order) if match]
        coffees = [match for match in re.findall(COFFEE_PATTERN, self.__order) if match]
        temperatures = [match for match in re.findall(TEMPERATURE_PATTERN, self.__order) if match]
        sweeteners = [match for match in re.findall(SWEETENER_PATTERN, self.__order) if match]
        flavors = [match for match in re.findall(FLAVOR_PATTERN, self.__order) if match]
        beverages = [match for match in re.findall(BEVERAGE_PATTERN, self.__order) if match]
        foods = [match for match in re.findall(FOOD_PATTERN, self.__order) if match]
        bakeries = [match for match in re.findall(BAKERY_PATTERN, self.__order) if match]
        add_ons = [match for match in re.findall(ADD_ONS_PATTERN, self.__order) if match]
        milk_types = [match for match in re.findall(MILK_PATTERN, self.__order) if match]
        allergies = [match for match in re.findall(COMMON_ALLERGIES_PATTERN, self.__order) if match]

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

    def __verify_quantities(
            self, order_type, order_details
    ) -> None:
        order_functions = {
            "coffee": (correct_coffee_order_quantities, ["add_ons", "sweeteners", "milk_type"]),
            "beverage": (correct_beverage_order_quantities, ["add_ons", "sweeteners"]),
            "food": (correct_food_order_quantities, []),
            "bakery": (correct_bakery_order_quantities, [])
        }

        if order_type in order_functions:
            correction, total_additions = order_functions[order_type]
            num_additions = sum(len(order_details[addition]) for addition in total_additions)
            min_length = len(order_details['quantities']) + num_additions
            if len(order_details['quantities']) < max(min_length, 1):
                order_details['quantities'] = correction(order_details, self.__order)


def split_transcription(
        order: str
) -> list[str]:
    """
    @rtype: list[str]
    @param order: original transcription
    @return: order split into 4 types: coffee, beverage, food, and bakery
    """
    start_time = time.time()
    split = re.split(SPLIT_PATTERN, order)
    remove_words = {'plus', 'get', 'and', 'also'}
    remove_chars = '[^a-zA-Z0-9]'

    filtered_order = [order for order in split
                      if order not in remove_words and order != remove_chars and order]

    logging.debug("split order time: %s", {time.time() - start_time})
    return filtered_order


def make_order_report(
        split_orders: list[str], connection_pool=None, embedding_cache: Redis = None,
        aws_connected: bool = False
) -> [list[dict]] and str:
    """
    @rtype: list[dict] and str
    @param split_orders: order split into 4 types: coffee, beverage, food, and bakery
    @param connection_pool: connection for postgres vector database
    @param embedding_cache: redis cache to reduce database queries
    @param aws_connected: flag to check if aws credentials are connected
    @return: all the orders and the str version for conversational AI model
    """
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

    logging.debug("make order report time: %s", time.time() - start_time)

    return order_report, ''.join(model_report)


# pylint: disable=too-many-arguments
def process_order(
        order, order_report, model_report, connection_pool,
        embedding_cache, aws_connected
) -> None:
    """
    @rtype: None
    @param order: one of the split orders
    @param order_report: pass by reference to append the final order
    @param model_report: pass by reference to append the final order
    @param connection_pool: connection for postgres vector database
    @param embedding_cache: redis cache to reduce database queries
    @param aws_connected: flag to check if aws credentials are connected
    @return: None because order_report and model_report are passed by reference
    """
    item_types = ['CoffeeItem', 'BeverageItem', 'FoodItem', 'BakeryItem']
    final_order = ((Order(order, connection_pool, embedding_cache, aws_connected).make_order()))

    if final_order:
        model_report.append(str(final_order))
        for item_type in item_types:
            if item_type in final_order:
                final_order[item_type].pop('common_allergies_in_item')
                final_order[item_type].pop('num_calories')
                break
        order_report.append(final_order)


def human_requested(
        transcription: str
) -> bool:
    """
    @rtype: bool
    @param transcription: transcription from customer
    @return: true if regex pattern is found in transcription
    """
    transcription = transcription.lower()
    pattern = (r'\b(human|person|employee|worker|staff member|manager|'
               r'owner|workman|hired help|crew member|agent)\b')
    return bool(re.search(pattern, transcription))


def accepted_deal(
        transcription: str
) -> bool:  # pragma: no cover
    """
    @rtype: bool
    @param transcription: transcription from customer
    @return: true if regex pattern is found in transcription
    """
    transcription = transcription.lower()
    pattern = r'\b(yes|yeah|sure|okay|ok|yup|yep|alright|fine|deal|k)\b'
    return bool(re.search(pattern, transcription[:4]))


if __name__ == "__main__":  # pragma: no cover
    total_time = time.time()

    key_file_path = path.join(path.dirname(path.realpath(__file__)),
                              "../../other/" + "openai_api_key.txt")
    with open(key_file_path, encoding='utf-8') as api_key:
        key = api_key.readline().strip()

    ORDER = ("two large cappuccinos with two sugars and two pumps of caramel"
             " then also two iced banana teas and finally add a glazed donuts"
             " and four blueberry muffins")

    split_order_time = time.time()
    details = split_transcription(ORDER)
    print(f"Split order time: {time.time() - split_order_time} seconds")
    print(details)

    make_order_report_time = time.time()
    report, model_version = make_order_report(details)
    print(f"Make order report time: {time.time() - make_order_report_time} seconds")

    print(report)

    end_time = time.time()
    execution_time = end_time - total_time
    print(f"Execution time: {execution_time} seconds")
