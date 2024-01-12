import re
import os
import threading
from os import path
import psycopg2.pool
from openai import OpenAI
from other.number_map import number_map
from src.vector_db.get_item import get_item
from src.vector_db.aws_database_auth import connection_string


role = """
            You are a fast food drive-thru worker at Dunkin' Donuts. Based on order transcription,
            and conversation history fill provide a response to the customer.
           """

prompt = """
        Give a response (ex. "Added to your cart! Is there anything else you'd like to order today?"
                        but make your own and somewhat personalize per order to sound normal) given transcription
                        and order details gathered from database:
        """


def conv_ai(transcription: str, order_report: str, conversation_history: str, api_key: str = None, print_token_usage: bool = False) -> str:
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\ntranscription: {transcription} + order details: {order_report}",
            },
            {
                "role": "system",
                "content": f"{role} and all previous conversation history: {conversation_history}",
            },
        ]
    )

    if print_token_usage:
        print(f"Prompt tokens ({response.usage.prompt_tokens}) + "
              f"Completion tokens ({response.usage.completion_tokens}) = "
              f"Total tokens ({response.usage.total_tokens})")
    return response.choices[0].message.content


class Order:
    def __init__(self, formatted_order: str):
        self.order: str = formatted_order.casefold().strip()
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
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())
        key_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "api_key.txt")
        with open(key_path) as KEY:
            self.key = KEY.readline().strip()


    def make_order(self) -> dict:
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


    def get_order_type(self) -> tuple[str, dict]:
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

    def make_coffee_order(self, order_details) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['coffee'][0]
        self.calculate_quantity(order_details['quantities'])
        self.temp = "" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.sweeteners.extend(order_details['sweeteners'])
        self.add_ons.extend(order_details['add_ons'])
        self.milk_type = "" if not order_details['milk_type'] else str(order_details['milk_type'])
        self.size = "" if not order_details['sizes'] else str(order_details['sizes'][0])
        self.get_price_and_num_calories()
        return {
            "MenuItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "temp": self.temp,
                "add_ons": self.add_ons,
                "milk_type": self.milk_type,
                "sweeteners": self.sweeteners,
                "num_calories": self.num_calories,
                "size": self.size,
                "cart_action": self.cart_action
            }
        }

    def make_beverage_order(self, order_details) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['beverage'][0]
        self.calculate_quantity(order_details['quantities'])
        self.temp = "" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.sweeteners = order_details['sweeteners']
        self.add_ons = order_details['add_ons']
        self.size = "" if not order_details['sizes'] else str(order_details['sizes'][0])
        self.get_price_and_num_calories()
        return {
            "MenuItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "temp": self.temp,
                "add_ons": self.add_ons,
                "sweeteners": self.sweeteners,
                "num_calories": self.num_calories,
                "size": self.size,
                "cart_action": self.cart_action
            }
        }

    def make_food_order(self, order_details) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['food'][0]
        self.calculate_quantity(order_details['quantities'])
        self.add_ons = order_details['add_ons']
        self.get_price_and_num_calories()
        return {
            "MenuItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "num_calories": self.num_calories,
                "cart_action": self.cart_action
            }
        }

    def make_bakery_order(self, order_details) -> dict:
        self.cart_action = self.get_cart_action()
        self.item_name = order_details['bakery'][0]
        self.calculate_quantity(order_details['quantities'])
        self.add_ons = order_details['add_ons']
        self.get_price_and_num_calories()
        return {
            "MenuItem": {
                "item_name": self.item_name,
                "quantity": self.quantity,
                "price": self.price,
                "num_calories": self.num_calories,
                "cart_action": self.cart_action
            }
        }

    def calculate_quantity(self, quantities) -> None:
        for quantity in quantities:
            quantity = number_map(quantity)
            if self.cart_action == "modification":
                self.quantity.append(-1 * quantity)
            else:
                self.quantity.append(quantity)

        return

    def get_cart_action(self) -> str:
        if self.is_question():
            return "question"
        elif self.is_modification():
            return "modification"
        else:
            return "insertion"

    def is_question(self) -> bool:
        pattern = r'\b(do you|how many|how much)\b'

        return bool(re.search(pattern, self.order))

    def is_modification(self) -> bool:
        pattern = r'\b(actually|dont want|remove|change|swap|adjust|modify)\b'

        return bool(re.search(pattern, self.order))

    def get_price_and_num_calories(self) -> None:
        # Create and start threads for each section
        item_thread = threading.Thread(target=self.process_item)
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

        return

    def process_item(self):
        item_details, _ = get_item(self.item_name, connection_pool=self.connection_pool, api_key=self.key)

        if self.cart_action == "question":
            self.quantity = []
            self.quantity.append(item_details[0][2])

        self.price.append(item_details[0][5])
        self.num_calories.append(item_details[0][4])

    def process_add_ons(self):
        for add_on in self.add_ons:
            add_on_details, _ = get_item(add_on, connection_pool=self.connection_pool, api_key=self.key)
            self.price.append(add_on_details[0][5])
            self.num_calories.append(add_on_details[0][4])
            if self.cart_action == "question":
                self.quantity.append(add_on_details[0][2])

    def process_sweeteners(self):
        for sweetener in self.sweeteners:
            sweetener_details, _ = get_item(sweetener, connection_pool=self.connection_pool, api_key=self.key)
            self.price.append(sweetener_details[0][5])
            self.num_calories.append(sweetener_details[0][4])
            if self.cart_action == "question":
                self.quantity.append(sweetener_details[0][2])

    def process_milk(self):
        if self.milk_type:
            milk_details, _ = get_item(self.milk_type, connection_pool=self.connection_pool, api_key=self.key)
            self.price.append(milk_details[0][5])
            self.num_calories.append(milk_details[0][4])
            if self.cart_action == "question":
                self.quantity.append(milk_details[0][2])

    def parse_order(self) -> dict:

        size_pattern = r'\b(small|medium|large|extra large)\b'
        coffee_pattern = r'\b(coffee|coffees|cappuccino|latte|americano|macchiato|frappuccino|\b(?<!shot of ' \
                         r')espresso)\b'
        quantity_pattern = r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen' \
                           r'|fifteen' \
                           r'|sixteen|seventeen|eighteen|nineteen|twenty|couple|few|dozen|a lot|a|an)\b'
        temperature_pattern = r'\b(hot|cold|iced|warm|room temp|extra hot)\b'
        sweetener_pattern = r'\b(sugar|honey|liquid cane sugar|sweet n low|equal|butter pecan|pink velvet|sugar ' \
                            r'packets)\b'
        flavor_pattern = r'\b(?!pump of )' + r'\b(vanilla|caramel|cinnamon|pumpkin spice|peppermint|chocolate|white ' \
                         r'chocolate chip|raspberry|blueberry|strawberry|peach|mango|banana|coconut|almond|hazelnut)\b'
        beverage_pattern = r'\b(water|tea|hot chocolate|hot cocoa|smoothie|juice|lemonade)\b'
        food_pattern = r'\b(egg and cheese croissant|egg and cheese|bacon egg and ' \
                       r'cheese|fruit|yogurt|oatmeal|croissant)\b'
        bakery_pattern = r'\b(bagel|pastry|cookie|brownie|cake|pie|croissant|muffin|muffins|glazed donut|glazed '\
                         r'donuts|strawberry donut|strawberry donuts|chocolate donut|chocolate donuts, boston cream)\b'
        add_ons_pattern = r'\b(shot of espresso|whipped cream|pump of caramel)\b'
        milk_pattern = r'\b(whole milk|two percent milk|one percent milk|skim milk|almond milk|oat milk|soy ' \
                       r'milk|coconut milk|half and half|heavy cream|cream)\b'

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
            "milk_type": milk_types
        }



def split_order(order) -> list[str]:
    split_pattern = r'\b(plus|get|and|also)\b(?! (a shot|a pump|cheese|sugar)\b)'
    split = re.split(split_pattern, order)
    remove_words = ['plus', 'get', 'and', 'also']
    remove_chars = '[^a-zA-Z0-9]'

    filtered_order = [order for order in split if order not in remove_words and order != remove_chars and order]

    return filtered_order


def make_order_report(split_orders: list[str]) -> [list[dict]]:
    order_report = []

    threads = []
    for order in split_orders:
        order_thread = threading.Thread(target=process_order, args=(order, order_report))
        threads.append(order_thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    return order_report


def process_order(order, order_report):
    order = ((Order(order).make_order()))

    if order:
        order_report.append(order)



if __name__ == "__main__":
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    orders = "How many glazed donuts do you have left and let me get a cappuccino with a shot of espresso"
    details = split_order(orders)

    print(details)

    report = make_order_report(details)

    print(report)
    # print(str(report))

    print(conv_ai(orders, str(report), "", print_token_usage=True, api_key=key))



