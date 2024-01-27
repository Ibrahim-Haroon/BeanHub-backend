import re
import time
import logging
import threading
from os import path
import psycopg2.pool
from redis import Redis
from os import getenv as env
from dotenv import load_dotenv
from other.number_map import number_map
from src.vector_db.get_item import get_item
from simpletransformers.ner import NERModel
from src.vector_db.aws_sdk_auth import get_secret
from src.vector_db.aws_database_auth import connection_string
from src.django_beanhub.settings import DEBUG

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
    ):
        init_time = time.time()
        self.order: str = formatted_order.casefold().strip()
        self.allergies: str = ""
        self.item_name: str = ""
        self.quantity: list[int] = []
        self.price: list[float] = []
        self.temp: str = ""
        self.add_ons: list[str] = []
        self.milk_type: str = ""
        self.sweeteners: list[str] = []
        self.num_calories: list[str] = []
        self.cart_action: str = ""
        self.size: str = ""
        if embedding_cache:
            self.embedding_cache = embedding_cache
        else:
            self.embedding_cache = None
        key_path = path.join(path.dirname(path.realpath(__file__)),
                             "../../other/" + "openai_api_key.txt")
        if path.exists(key_path):
            with open(key_path) as KEY:
                self.key = KEY.readline().strip()
        else:
            self.key = env('OPENAI_API_KEY')
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
        order_type, order_details = self.get_order_type()

        if order_type == "coffee":
            return self.make_coffee_order(order_details)
        elif order_type == "beverage":
            return self.make_beverage_order(order_details)
        elif order_type == "food":
            return self.make_food_order(order_details)
        elif order_type == "bakery":
            return self.make_bakery_order(order_details)

        return {}

    def get_order_type(
            self
    ) -> tuple[str, dict]:
        order_details = self.parse_order()

        if order_details['coffee']:
            return "coffee", order_details
        elif order_details['beverage']:
            return "beverage", order_details
        elif order_details['food']:
            return "food", order_details
        elif order_details['bakery']:
            return "bakery", order_details

        return "", {}

    def make_coffee_order(
            self, order_details
    ) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['coffee'][0]
        self.calculate_quantity(order_details['quantities'])
        self.temp = "regular" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.sweeteners.extend(order_details['sweeteners'])
        self.add_ons.extend(order_details['add_ons'])
        self.milk_type = "regular" if not order_details['milk_type'] else str(order_details['milk_type'][0])
        self.size = "regular" if not order_details['sizes'] else str(order_details['sizes'][0])
        self.get_price_and_allergies_and_num_calories()
        return {
            "CoffeeItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "temp": self.temp,
                "add_ons": self.add_ons,
                "milk_type": self.milk_type,
                "sweeteners": self.sweeteners,
                "num_calories": self.num_calories,
                "size": self.size,
                "cart_action": self.cart_action,
                "common_allergies_in_item": self.allergies
            }
        }

    def make_beverage_order(
            self, order_details
    ) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['beverage'][0]
        self.calculate_quantity(order_details['quantities'])
        self.temp = "regular" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.sweeteners = order_details['sweeteners']
        self.add_ons = order_details['add_ons']
        self.size = "regular" if not order_details['sizes'] else str(order_details['sizes'][0])
        self.get_price_and_allergies_and_num_calories()
        return {
            "BeverageItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "temp": self.temp,
                "add_ons": self.add_ons,
                "sweeteners": self.sweeteners,
                "num_calories": self.num_calories,
                "size": self.size,
                "cart_action": self.cart_action,
                "common_allergies_in_item": self.allergies
            }
        }

    def make_food_order(
            self,
            order_details
    ) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['food'][0]
        self.calculate_quantity(order_details['quantities'])
        self.get_price_and_allergies_and_num_calories()
        return {
            "FoodItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "num_calories": self.num_calories,
                "cart_action": self.cart_action,
                "common_allergies_in_item": self.allergies
            }
        }

    def make_bakery_order(
            self,
            order_details
    ) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['bakery'][0]
        self.calculate_quantity(order_details['quantities'])
        self.get_price_and_allergies_and_num_calories()
        return {
            "BakeryItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "num_calories": self.num_calories,
                "cart_action": self.cart_action,
                "common_allergies_in_item": self.allergies
            }
        }

    def calculate_quantity(
            self,
            quantities
    ) -> None:
        for quantity in quantities:
            quantity = number_map(quantity)
            if self.cart_action == "modification":
                self.quantity.append(-1 * quantity)
            else:
                self.quantity.append(quantity)

        return

    def get_cart_action(
            self
    ) -> str:
        if self.is_question():
            return "question"
        elif self.is_modification():
            return "modification"
        else:
            return "insertion"

    def is_question(
            self
    ) -> bool:
        pattern = r'\b(do you|how many|how much|does|what are)\b'

        return bool(re.search(pattern, self.order))

    def is_modification(
            self
    ) -> bool:
        pattern = (r'\b(actually remove|actually change|dont want|don\'t want|remove|change|swap|adjust|modify|take '
                   r'away|replace)\b')

        return bool(re.search(pattern, self.order))

    def get_price_and_allergies_and_num_calories(
            self
    ) -> None:
        db_time = time.time()

        item_thread = threading.Thread(target=self.process_item_and_allergies)
        add_ons_thread = threading.Thread(target=self.process_add_ons)
        sweeteners_thread = threading.Thread(target=self.process_sweeteners)
        milk_thread = threading.Thread(target=self.process_milk)

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

    def process_item_and_allergies(
            self
    ) -> None:
        item_details, _ = get_item(self.item_name,
                                   connection_pool=self.connection_pool,
                                   embedding_cache=self.embedding_cache if self.embedding_cache else None,
                                   api_key=self.key)

        if self.cart_action == "question":
            self.quantity.append(item_details[0][2])

        self.allergies = item_details[0][3]
        self.price.append(item_details[0][5])
        self.num_calories.append(item_details[0][4])

    def process_add_ons(
            self
    ) -> None:
        for add_on in self.add_ons:
            add_on_details, _ = get_item(add_on,
                                         connection_pool=self.connection_pool,
                                         embedding_cache=self.embedding_cache if self.embedding_cache else None,
                                         api_key=self.key)
            self.price.append(add_on_details[0][5])
            self.num_calories.append(add_on_details[0][4])
            if self.cart_action == "question":
                self.quantity.append(add_on_details[0][2])

    def process_sweeteners(
            self
    ) -> None:
        for sweetener in self.sweeteners:
            sweetener_details, _ = get_item(sweetener,
                                            connection_pool=self.connection_pool,
                                            embedding_cache=self.embedding_cache if self.embedding_cache else None,
                                            api_key=self.key)
            self.price.append(sweetener_details[0][5])
            self.num_calories.append(sweetener_details[0][4])
            if self.cart_action == "question":
                self.quantity.append(sweetener_details[0][2])

    def process_milk(
            self
    ) -> None:
        if self.milk_type and self.milk_type != "regular":
            milk_details, _ = get_item(self.milk_type,
                                       connection_pool=self.connection_pool,
                                       embedding_cache=self.embedding_cache if self.embedding_cache else None,
                                       api_key=self.key)
            self.price.append(milk_details[0][5])
            self.num_calories.append(milk_details[0][4])
            if self.cart_action == "question":
                self.quantity.append(milk_details[0][2])

    def parse_order(
            self
    ) -> dict:

        size_pattern = r'\b(small|medium|large|extra large)\b'

        coffee_pattern = (
            r'\b(coffee|black coffee|coffees|cappuccino|latte|americano|macchiato|'
            r'frappuccino|chai latte|espresso)(?<!shot of)\b'
        )

        quantity_pattern = (
            r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|'
            r'fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|couple|few|'
            r'dozen|a lot|a|an)\b'
        )

        temperature_pattern = r'\b(hot|cold|iced|warm|room temp|extra hot)\b'

        sweetener_pattern = (
            r'\b(sugar|honey|liquid cane sugar|sweet n low|equal|butter pecan|pink velvet|'
            r'sugar packets)\b'
        )

        flavor_pattern = (
            r'\b(?!pump of |pumps of )'
            r'(vanilla|caramel|cinnamon|pumpkin|espresso spice|peppermint|chocolate|white '
            r'raspberry|blueberry|strawberry|peach|mango|banana|coconut|almond|hazelnut)\b'
        )

        beverage_pattern = (
            r'\b(water|tea|hot chocolate|hot cocoa|apple juice|orange juice|cranberry juice|'
            r'mango smoothie|pineapple smoothie|pina colada smoothie|vanilla milkshake|'
            r'lemon tea|mango tea|jasmine|green tea|mint tea)\b'
        )

        food_pattern = (
            r'\b(egg and cheese croissant|egg and cheese|bacon egg and cheese|fruit|yogurt|'
            r'oatmeal|egg and cheese on croissant|hashbrown|hashbrowns|hash brown|hash '
            r'browns|grilled cheese|egg and cheese on english muffin|plain bagel|'
            r'everything bagel|sesame bagel|asiago bagel)\b'
        )

        bakery_pattern = (
            r'\b(brownie|blueberry muffin|blueberry muffins|glazed donut|glazed donuts|'
            r'strawberry donut|strawberry donuts|chocolate donut|chocolate donuts|donut|'
            r'boston cream donuts|boston cream|lemon cake|chocolate chip muffin)\b'
        )

        add_ons_pattern = (
            r'\b(shot of espresso|whipped cream|pump of caramel|pumps of caramel|pump of '
            r'vanilla|pumps of vanilla|pump of sugar|pumps of sugar|liquid sugar|pump of '
            r'butter pecan|pumps of butter pecan)\b'
        )

        milk_pattern = (
            r'\b(whole milk|two percent milk|one percent milk|skim milk|almond milk|oat milk|'
            r'soy milk|coconut milk|half and half|heavy cream|cream)\b'
        )

        common_allergies = (
            r'\b(peanuts|tree nuts|tree nut|shellfish|fish|wheat|soy|eggs|milk|gluten|dairy|'
            r'lactose|sesame|mustard|sulfates)\b'
        )

        sizes = re.findall(size_pattern, self.order)
        quantities = re.findall(quantity_pattern, self.order)
        coffees = re.findall(coffee_pattern, self.order)
        temperatures = re.findall(temperature_pattern, self.order)
        sweeteners = re.findall(sweetener_pattern, self.order)
        flavors = re.findall(flavor_pattern, self.order)
        beverages = re.findall(beverage_pattern, self.order)
        foods = re.findall(food_pattern, self.order)
        bakeries = re.findall(bakery_pattern, self.order)
        add_ons = re.findall(add_ons_pattern, self.order)
        milk_types = re.findall(milk_pattern, self.order)
        allergies = re.findall(common_allergies, self.order)

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
    split_pattern = r'\b(plus|get|and|also)\b(?! (a shot|a pump|whipped|cheese|sugar|cream|one|two|three|wait)\b)'
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
    pattern = r'\b(human|person|employee|worker|staff member|manager|owner|workman|hired help|crew member|agent)\b'
    return bool(re.search(pattern, transcription))


if __name__ == "__main__":
    total_time = time.time()

    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "openai_api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    orders = "Can I have one black coffee with a pump of caramel"

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
