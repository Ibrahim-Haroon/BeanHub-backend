import os
import time
import httpx
import logging
import asyncio
from os import path

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

role = """
            You are a fast food drive-thru worker at Dunkin' Donuts. Based on order transcription,
            and conversation history fill provide a response to the customer.
           """

prompt = """
        Give a response (ex. "Added to your cart! Is there anything else you'd like to order today?"
                        but make your own and somewhat personalize per order to sound normal) given transcription
                        and order details gathered from the database:
        """


async def get_openai_response(client, model, messages, api_key):
    try:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json={"model": model, "messages": messages},
            headers={"Authorization": f"Bearer {api_key}"}
        )

        return response.json()
    except Exception as e:
        logging.error(f"*****TIME OUT*******\nError: {e}")
        return {"choices": [{"message": {"content": "Added to your order! Anything else?"}}]}

async def conv_ai_async(transcription: str, order_report: str, conversation_history: str, api_key: str = None):
    if api_key is None:
        api_key = os.environ['OPENAI_API_KEY']

    async with httpx.AsyncClient() as client:
        response = await get_openai_response(
            client,
            "gpt-3.5-turbo-1106",
            [{"role": "system", "content": f"{role} and all previous conversation history: {conversation_history}"},
             {"role": "user", "content": f"{prompt}\ntranscription: {transcription} + order details: {order_report}"}],
            api_key
        )
        return response['choices'][0]['message']['content']


def conv_ai(transcription: str, order_report: str, conversation_history: str, api_key: str = None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    start_time = time.time()
    response = loop.run_until_complete(conv_ai_async(transcription, order_report, conversation_history, api_key))
    logging.info(f"conv_ai time: {time.time() - start_time}")

    loop.close()

    return response


def main():
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    start_time = time.time()
    response = conv_ai(transcription="Let me get a latte with two pumps of caramel and sugar",
                       order_report="""
                    [{'MenuItem': {'item_name': 'latte', 'quantity': [1, 2], 'price': [5.0, 10.0, 2.0], 
                    'temp': 'regular', 'add_ons': ['pumps of caramel'], 'milk_type': 'regular', 'sweeteners': [
                    'sugar'], 'num_calories': ['(120,180)', '(60,120)', '(200,500)'], 'size': 'regular', 
                    'cart_action': 'insertion'}}]
                            """,
                       conversation_history="",
                       api_key=key)
    print(f"conv_ai time: {time.time() - start_time}")
    print(type(response))
    return response


if __name__ == "__main__":
    main()
