"""
This file is used to interact with the OpenAI API for text generation.
"""
# pylint: disable=R0801
import sys
from os import path
from os import getenv as env
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def openai_text_api(
        prompt: str, api_key: str = None, model_behavior: str = None
) -> str:
    """

    @rtype: str
    @param prompt: str = question
    @param api_key: str = auth key for OpenAI
    @param model_behavior: str = needed if want model to imitate something specific (i.e. doctor)
    @return: response to question
    """

    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=env('OPENAI_API_KEY'))

    if model_behavior:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": model_behavior
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4-1106-preview",
        )
    else:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4-1106-preview",
        )

    return response.choices[0].message.content


def main(
        prompts: list[str]
) -> int:  # pragma: no cover
    """
    @rtype: int
    @param prompts: str = list of questions for gpt
    @return: 0 if successful
    """
    key_file_path = path.join(path.dirname(path.realpath(__file__)),
                              "../../other/" + "openai_api_key.txt")
    with open(key_file_path, encoding='utf-8') as api_key:
        _ = api_key.readline().strip()

    for prompt in tqdm(prompts):
        prompt = prompt.strip()

        response = openai_text_api(prompt)

        print("question: " + prompt + " response: " + response)

    return 0


if __name__ == "__main__":  # pragma: no cover
    input_file_path = path.join(path.dirname(path.realpath(__file__)),
                                "../IO", "input.txt")
    output_file_path = path.join(path.dirname(path.realpath(__file__)),
                                 "../IO", "output.txt")

    with open(input_file_path, 'r', encoding='utf-8') as f:
        sys.stdin = f
    with open(output_file_path, 'w', encoding='utf-8') as f:
        sys.stdout = f

    istream = []

    for line in sys.stdin:
        istream.append(line)

    main(["hi"])
