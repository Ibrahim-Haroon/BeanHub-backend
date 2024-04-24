"""
This script demonstrates how to call a function from ChatGPT.
"""
import json
from openai import OpenAI


def hello_world(
        append_string
) -> str:
    """
    @rtype: str
    @param append_string: The string to append to the hello world message
    @return: Hello World! appended with the string
    """
    hello = "Hello World! " + append_string
    return hello


API_KEY = ""
client = OpenAI(api_key=API_KEY)


# pylint: disable=unused-argument
def call_chat_gpt_with_functions(
        append_string
) -> None:
    """
    @rtype: None
    @param append_string: The string to append to the hello world message
    """
    messages = [
        {
            "role": "system",
            "content": "Perform function requests for the user",
        },
        {
            "role": "user",
            "content": "Hello, I am a user, I would like to call the"
                       " hello world function passing the string 'It's"
                       " about time!' to it.",
        },
    ]

    # Step 1: Call ChatGPT with the function name
    chat = client.chat.completions.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=[
            {
                "name": "helloWorld",
                "description": "Prints hello world with the string passed to it",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appendString": {
                            "type": "string",
                            "description": "The string to append to the hello world message",
                        },
                    },
                    "required": ["appendString"],
                },
            }
        ],
        function_call="auto",
    )

    wants_to_use_function = chat.choices[0].finish_reason == "function_call"
    content = ""

    # Step 2: Check if ChatGPT wants to use a function
    if wants_to_use_function:
        # Step 3: Use ChatGPT arguments to call your function
        if chat.choices[0].message.function_call.name == "helloWorld":
            argument_obj = chat.choices[0].message.function_call.arguments
            argument_obj = json.loads(argument_obj)  # Convert JSON string to Python dictionary
            print(f"arg obj = {argument_obj}")
            content = hello_world(argument_obj["appendString"])
            messages.append(chat.choices[0].message)
            messages.append(
                {
                    "role": "function",
                    "name": "helloWorld",
                    "content": content,
                }
            )

    # Step 4: Call ChatGPT again with the function response
    step4_response = client.chat.completions.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
    )
    print(step4_response.choices[0].message.content)


# Call the ChatGPT function
call_chat_gpt_with_functions('It\'s about time!')
