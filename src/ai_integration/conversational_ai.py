import os
import json
from os import path
from openai import OpenAI
from src.ai_integration.nlp_bert import ner_transformer

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
                                                but make your own, however if it is a question then dont give a
                                                definitive answer like "sorry we have no more" or "sorry we are out of
                                                 stock", but rather "let me check" or "let me see if we have any more)
        """


def conv_ai(transcription: str, tagged_sentence: list, conversation_history, api_key: str = None, print_token_usage: bool = False) -> json:
    role = """
            You are a fast food drive-thru worker at Dunkin' Donuts. Based on order transcription, 
            NER tags, and conversation history fill in json object. Also generate a customer-facing response. 
            Follow these templates for json object, if one is not found then put 'None'. 
            Be precise for internal response.
           """


    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": f"{role} + \nconversation history: f{conversation_history} + "
                           f"\n\nMUST GIVE CUSTOMER FACING RESPONSE EACH AND EVERY TIME."
            },
            {
                "role": "user",
                "content": f"{prompt} + \ntranscription: {transcription} + \ntagged sentences: {tagged_sentence}",
            },
        ]
    )

    if print_token_usage:
        print(f"Prompt tokens ({response.usage.prompt_tokens}) + "
              f"Completion tokens ({response.usage.completion_tokens}) = "
              f"Total tokens ({response.usage.total_tokens})")
    return response.choices[0].message.content


def main() -> int:
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    transcription = "Do you guys have any more glazed donuts?"
    ner_tags = ner_transformer(transcription)
    print(ner_tags)
    conversation_history = ""

    res = json.loads(conv_ai(transcription, ner_tags, conversation_history, api_key=key, print_token_usage=True))

    print(res)

    return 0


if __name__ == "__main__":
    main()

