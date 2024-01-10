import os
import json
from os import path
from openai import OpenAI
from src.vector_db.contain_item import contains_quantity
from src.ai_integration.nlp_bert import ner_transformer

role = """
            You are a fast food drive-thru worker at Dunkin' Donuts. Based on order transcription,
            NER tags, and conversation history fill in json object. Also generate a customer-facing response.
            Follow these templates for json object, if one is not found then put 'None'.
            Be precise for internal response.
           """

prompt = """provide a structured json object.
            Follow these formatting guidelines for internal response:
            COFFEE_ORDER: “action" (insertion, deletion, modification, question),
            "coffee_type" (black coffee, latte, cappuccino, etc.),
            "coffee_flavor" (caramel, hazelnut, etc. (but different from pump of caramel),
            "size" (small, large, medium, venti, grande, etc.), "quantity" (integer), "temp" (iced, hot, warm, etc.),
            "add_ons" (pump of caramel, shot of x, whipped cream, etc.),
            "milk_type" (soy milk, whole milk, skim milk, etc.), "sweetener" (honey, sugar, etc.)
            BEVERAGE_ORDER: "action" (insertion, deletion, modification, question),
            "beverage_type" (water, tea, soda, smoothie, etc.) "size" (small, large, medium, venti, grande, etc.),
            "quantity" (integer), "temp" (iced, hot, warm, etc.), "add_ons" (whipped cream, syrup, etc.)
            "sweetener" (honey, sugar, etc.)
            FOOD_ORDER: "action" (insertion, deletion, modification, question),
            "food_item" (egg and cheese, hash browns, etc.),"quantity" (integer)
            BAKERY_ORDER: "action" (insertion, deletion, modification, question), "bakery_item" (donuts, cakes, etc.),
            "quantity" (integer)
            CUSTOMER_RESPONSE: "response" (ex. "Added to your cart! Is there anything else you'd like to order today?"
                                                but make your own and somewhat personalize per order to sound normal,
                                                however if it is a question then use contains_quantity function 
                                                to check database and make sure there is a enough quantity, never guess.
        """


def conv_ai(transcription: str, tagged_sentence: list, conversation_history, api_key: str = None, print_token_usage: bool = False) -> json:
    messages = [
            {
                "role": "system",
                "content": f"{role} + conversation history: f{conversation_history} + "
                           f"MUST GIVE CUSTOMER FACING RESPONSE EACH AND EVERY TIME."
            },
            {
                "role": "user",
                "content": f"{prompt} + \ntranscription: {transcription} + \ntagged sentences: {tagged_sentence}",
            },
        ]

    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        response_format={"type": "json_object"},
        functions=[
            {
                "name": "contains_quantity",
                "description": "Get the quantity of an item from database for when user asks a questions"
                               " such as \"Do you have any more XYZ\" or \"How many of XYZ do you have?\"",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order": {
                            "type": "string",
                            "description": "The name of the item to get the quantity of such as \" glazed donut\"",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "The quantity of the item to get such as 1",
                        },
                    },
                    "required": ["order", "quantity"],
                },
            }
        ],
        function_call="auto",
    )

    use_function = response.choices[0].finish_reason == "function_call"

    if use_function:
        if response.choices[0].message.function_call.name == "contains_quantity":
            argument_obj = response.choices[0].message.function_call.arguments
            argument_obj = json.loads(argument_obj)
            print(f"arg obj = {argument_obj}")
            content = contains_quantity(argument_obj["order"], argument_obj["quantity"])
            messages.append(response.choices[0].message)
            messages.append(
                {
                    "role": "function",
                    "name": "contains_quantity",
                    "content": content,
                }
            )

    final_response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        response_format={"type": "json_object"}
    )

    if print_token_usage:
        print(f"Prompt tokens ({response.usage.prompt_tokens + final_response.usage.prompt_tokens}) + "
              f"Completion tokens ({response.usage.completion_tokens + final_response.usage.completion_tokens}) = "
              f"Total tokens ({response.usage.total_tokens + + final_response.usage.total_tokens})")
    return final_response.choices[0].message.content


def main() -> int:
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    transcription = "How many lattes do you have left also can I get a glazed donut"
    ner_tags = ner_transformer(transcription)
    print(ner_tags)
    conversation_history = ""

    res = (conv_ai(transcription, ner_tags, conversation_history, api_key=key, print_token_usage=True))

    print(res)

    return 0


if __name__ == "__main__":
    main()

