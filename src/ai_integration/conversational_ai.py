import time
import logging
from os import path
from openai import OpenAI
from os import getenv as env
from dotenv import load_dotenv
from src.django_beanhub.settings import DEBUG

logging_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()

role = """
        You are a fast food drive-thru worker at Aroma Joe's. Response should be formed solely based on
        on order details and conversation history. Don't add items to cart if cart action is # question # and check all
        attributes of the order details, such as quantity, price, num_calories, allergies, etc. If the customer asks a
        question
       """

prompt = """
        Give a response (ex. "Added to your cart! Is there anything else you'd like to order today?"
                        but make your own and somewhat personalize per order to sound normal) given transcription
                        and order details gathered from the database:
        """


def conv_ai(
        transcription: str, order_report: str, conversation_history: str, deal: str | None = None,
        api_key: str = None, max_tokens: int = 200
) -> str:  # pragma: no cover
    if api_key is None:
        api_key = env('OPENAI_API_KEY')

    start_time = time.time()
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {
                "role": "system",
                "content": (f"{role} and all previous conversation history: {conversation_history}."
                            if deal is None
                            else f"{role} and all previous conversation history: {conversation_history} "
                                 f"and remember to upsell customer with deal: {deal}"
                            ),
            },
            {
                "role": "user",
                "content": f"{prompt}\ntranscription: {transcription} + order details: {order_report}"
            }
        ],
        max_tokens=max_tokens,
        stream=True
    )

    for chunk in response:
        yield chunk.choices[0].delta.content

    logging.debug(f"conv_ai time: {time.time() - start_time}")


def main(

) -> None:  # pragma: no cover
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "openai_api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    start_time = time.time()
    for _ in conv_ai(
            transcription="Can I get one smoothie please",
            order_report="""
                   ([{'BeverageItem': {'item_name': 'smoothie', 'quantity': [1], 'price': [5.0], 'temp': 'regular',
                    'add_ons': [], 'sweeteners': [], 'num_calories': ['(200,200)'], 'size': 'regular',
                     'cart_action': 'insertion', 'common_allergies_in_item': ['Nuts, Dairy, Soy, Gluten']}}], '')

                            """,
            conversation_history="",
            deal="Get a glazed donut for $1 more",
            api_key=key):
        print(_)
    print(f"conv_ai time: {time.time() - start_time}")


if __name__ == "__main__":  # pragma: no cover
    main()
