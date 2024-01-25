import os
import time
import httpx
import logging
import asyncio
from os import path
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


async def get_openai_response(
        client, model, messages, api_key, max_tokens: int | None = None
) -> dict:
    try:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json={"model": model, "messages": messages, "max_tokens": max_tokens, "n": 1},
            headers={"Authorization": f"Bearer {api_key}"}
        )

        return response.json()
    except Exception as e:
        logging.error(f"*****TIME OUT*******\nError: {e}")
        return {"choices": [{"message": {"content": "Added to your order! Anything else?"}}]}


async def conv_ai_async(
        transcription: str, order_report: str, conversation_history: str, deal: str | None = None,
        api_key: str = None, max_tokens: int | None = None, print_token_usage: bool = False
) -> str:
    if api_key is None:
        api_key = os.environ['OPENAI_API_KEY']

    async with httpx.AsyncClient() as client:
        response = await get_openai_response(
            client,
            "gpt-3.5-turbo-1106",
            [
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
            api_key,
            max_tokens
        )
        if print_token_usage:
            print(f"Prompt tokens ({response['usage']['prompt_tokens']}) + "
                  f"Completion tokens ({response['usage']['completion_tokens']}) = "
                  f"Total tokens ({response['usage']['total_tokens']})")

        return response['choices'][0]['message']['content']


def conv_ai(
        transcription: str, order_report: str, conversation_history: str, deal: str | None = None,
        api_key: str = None, max_tokens: int = 200, print_token_usage: bool = False
) -> str:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if api_key is None:
        api_key = env('OPENAI_API_KEY')

    start_time = time.time()
    response = loop.run_until_complete(
        conv_ai_async(transcription, order_report, conversation_history, deal, api_key, max_tokens, print_token_usage))
    logging.debug(f"conv_ai time: {time.time() - start_time}")

    loop.close()

    return response


def main(

) -> str:
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "openai_api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    start_time = time.time()
    response = conv_ai(
        transcription="Can I get one smoothie please",
        order_report="""
                   ([{'BeverageItem': {'item_name': 'smoothie', 'quantity': [1], 'price': [5.0], 'temp': 'regular',
                    'add_ons': [], 'sweeteners': [], 'num_calories': ['(200,200)'], 'size': 'regular',
                     'cart_action': 'insertion', 'common_allergies_in_item': ['Nuts, Dairy, Soy, Gluten']}}], '')

                            """,
        conversation_history="",
        deal="Get a glazed donut for $1 more",
        api_key=key,
        print_token_usage=True)
    print(f"conv_ai time: {time.time() - start_time}")
    print(response)
    return response


if __name__ == "__main__":
    main()
