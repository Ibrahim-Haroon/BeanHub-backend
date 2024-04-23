"""
script to get conversational ai response from gpt model
"""
import time
import logging
from os import path
from os import getenv as env
from openai import OpenAI
from dotenv import load_dotenv
from src.django_beanhub.settings import DEBUG

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()

ROLE = """
        You are a fast food drive-thru worker at Aroma Joe's. Response should be formed solely based on
        on order details and conversation history. Don't add items to cart if cart action is # question # and check all
        attributes of the order details, such as quantity, price, num_calories, allergies, etc. If the customer asks a
        question
       """

PROMPT = """
        Give a response (ex. "Added to your cart! Is there anything else you'd like to order today?"
                        but make your own and somewhat personalize per order to sound normal) given transcription
                        and order details gathered from the database:
        """


# pylint: disable=too-many-arguments
def conv_ai(
        transcription: str, order_report: str, conversation_history: str, deal: str | None = None,
        api_key: str = None, max_tokens: int = 200
) -> str:
    """
    @rtype: str
    @param transcription: complete transcription of the customer's order
    @param order_report: parsed order details from the transcription
    @param conversation_history: all previous conversation history
    @param deal: most relevant deal to offer customer
    @param api_key: openi api key
    @param max_tokens: control the length of the response
    """
    if api_key is None:
        api_key = env('OPENAI_API_KEY')

    start_time = time.time()

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {
                "role": "system",
                "content": (f"{ROLE} and all previous conversation history: "
                            f"{conversation_history}."
                            if deal is None
                            else f"{ROLE} and all previous conversation history:"
                                 f" {conversation_history} "
                                 f"and remember to upsell customer with deal: {deal}"
                            ),
            },
            {
                "role": "user",
                "content": f"{PROMPT}\n"
                           f"transcription: {transcription}"
                           f" + order details: {order_report}"
            }
        ],
        max_tokens=max_tokens,
        stream=True
    )

    for chunk in response:  # pylint: disable=E1133
        yield chunk.choices[0].delta.content

    logging.debug("conv_ai time: %s", (time.time() - start_time))


# pylint: disable=too-many-arguments
def local_conv_ai(
        transcription: str, order_report: str, conversation_history: str, deal: str | None = None,
        api_key: str = "sk-no-key-required"
) -> str:
    """
    @rtype: str
    @param transcription: complete transcription of the customer's order
    @param order_report: parsed order details from the transcription
    @param conversation_history: all previous conversation history
    @param deal: most relevant deal to offer customer
    @param api_key: just to keep format consistent with conv_ai, but not used
    """

    client = OpenAI(
        base_url="http://localhost:8080/v1",
        api_key=api_key
    )

    response = client.chat.completions.create(
        model='llama-2-13b-chat.Q4_K_M.gguf',
        messages=[
            {
                "role": "system",
                "content": (f"{ROLE} and all previous conversation history:"
                            f" {conversation_history} "
                            f"and remember to upsell customer with deal: {deal}"
                            ),
            },
            {
                "role": "user",
                "content": f"{PROMPT}\n"
                           f"transcription: {transcription}"
                           f" + order details: {order_report}"
            }
        ],
        stream=True
    )

    for chunk in response:  # pylint: disable=E1133
        yield chunk.choices[0].delta.content


def main(

) -> None:  # pragma: no cover
    """
    @rtype: None
    @return: 0 if successful
    """
    key_path = path.join(path.dirname(path.realpath(__file__)), "../..",
                         "other", "openai_api_key.txt")
    with open(key_path, encoding='utf-8') as api_key:
        key = api_key.readline().strip()

    start_time = time.time()
    for _ in local_conv_ai(
            transcription="Can I get one smoothie please",
            order_report="""
                   ([{'BeverageItem': {'item_name': 'smoothie', 'quantity': [1], 'price': [5.0], 'temp': 'regular',
                    'add_ons': [], 'sweeteners': [], 'num_calories': ['(200,200)'], 'size': 'regular',
                     'cart_action': 'insertion', 'common_allergies_in_item': ['Nuts, Dairy, Soy, Gluten']}}], '')

                            """,
            conversation_history="",
            deal="Get a glazed donut for $1 more",
            api_key=key
    ):
        print(_)
    print(f"conv_ai time: {time.time() - start_time}")


if __name__ == "__main__":  # pragma: no cover
    main()
