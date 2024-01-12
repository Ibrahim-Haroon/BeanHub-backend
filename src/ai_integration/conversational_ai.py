import re
import os
from openai import OpenAI
from other.number_map import number_map

role = """
            You are a fast food drive-thru worker at Dunkin' Donuts. Based on order transcription,
            and conversation history fill provide a response to the customer.
           """

prompt = """
        Give a response (ex. "Added to your cart! Is there anything else you'd like to order today?"
                        but make your own and somewhat personalize per order to sound normal) given transcription
                        and order details gathered from database:
        """


def conv_ai(transcription: str, order_details: str, conversation_history: str, api_key: str = None, print_token_usage: bool = False) -> str:
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\ntranscription: {transcription} + order details: {order_details}",
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
        self.item_name = order_details['coffee']
        self.calculate_quantity(order_details['quantities'])
        self.price.append(2.99)
        self.temp = "" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.sweeteners.extend(order_details['sweeteners'])
        self.add_ons.extend(order_details['add_ons'])
        self.milk_type = "" if not order_details['milk_type'] else str(order_details['milk_type'])
        self.num_calories.append('(60, 120)')
        self.size = "" if not order_details['sizes'] else str(order_details['sizes'][0])
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
        self.price.append(2.99)
        self.temp = "" if not order_details['temperature'] else str(order_details['temperature'][0])
        self.sweeteners = order_details['sweeteners']
        self.add_ons = order_details['add_ons']
        self.num_calories.append('(60, 120)')
        self.size = "" if not order_details['sizes'] else str(order_details['sizes'][0])
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
        self.price.append(2.99)
        self.add_ons = order_details['add_ons']
        self.num_calories.append('(60, 120)')
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
        self.price.append(2.99)
        self.add_ons = order_details['add_ons']
        self.num_calories.append('(60, 120)')
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

    def parse_order(self) -> dict:

        size_pattern = r'\b(small|medium|large|extra large)\b'
        coffee_pattern = r'\b(coffee|coffees|cappuccino|latte|americano|macchiato|frappuccino|\b(?<!shot of )espresso)\b'
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

        # Find matches in the order
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
    split_pattern = r'\b(plus|get|and|also)\b(?! (a shot|a pump|cheese)\b)'
    split = re.split(split_pattern, order)
    remove_words = ['plus', 'get', 'and', 'also']
    remove_chars = '[^a-zA-Z0-9]'

    filtered_order = [order for order in split if order not in remove_words and order != remove_chars and order]

    return filtered_order


def make_order_report(split_orders: list[str]) -> tuple[list[dict], str]:
    order_details = ""
    order_report = []

    for order in split_orders:
        order = ((Order(order).make_order()))
        order_details += str(order) + "\n"
        order_report.append(order)

    return order_report, order_details


from os import path


if __name__ == "__main__":
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    orders = "I'd like an egg and cheese and a small coffee and do you have anymore glazed donuts."
    details = split_order(orders)

    print(details)

    report, details = make_order_report(details)


    print(conv_ai(orders, details, "", print_token_usage=True, api_key=key))



