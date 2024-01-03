from openai import OpenAI
import sys
from tqdm import tqdm
from os import path



def openai_text_api(prompt: str, api_key: str = None, model_behavior: str = None) -> str:
    """

    @rtype: str
    @param prompt: str = question
    @param api_key: str = key to validate OpenAI api call
    @param model_behavior: str = needed if want model to imitate something specific (i.e. doctor)
    @return: response to question
    """

    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI()

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


def main(prompts: list[str]) -> int:
    """
    @rtype: int
    @param prompts: str = list of questions for gpt
    @return: 0 if successful
    """
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    for prompt in tqdm(prompts):
        prompt = prompt.strip()

        response = openai_text_api(prompt, key)

        print("question: " + prompt + " response: " + response)

    return 0


if __name__ == "__main__":
    input_file_path = path.join(path.dirname(path.realpath(__file__)), "../IO", "input.txt")
    output_file_path = path.join(path.dirname(path.realpath(__file__)), "../IO", "output.txt")

    sys.stdin = open(input_file_path, 'r')
    sys.stdout = open(output_file_path, 'w')

    istream = []

    for line in sys.stdin:
        istream.append(line)

    main(istream)