import os
from os import path
from openai import OpenAI


def openai_text_to_speech_api(text: str, api_key: str = None, audio_file_path: str = None) -> bytes:
    """

    @rtype: bytes
    @param text: desired text to convert into audio
    @param api_key: key for OpenAI auth
    @param audio_file_path: file path to save if wanted
    @return audio
    """
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text

    )

    if audio_file_path:
        response.stream_to_file(audio_file_path)

    return response.content


def main(text: str) -> int:
    key_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "openai_api_key.txt")
    with open(key_file_path) as api_key:
        key = api_key.readline().strip()

    openai_text_to_speech_api(text, key)

    return 0


if __name__ == "__main__":
    input_file_path = path.join(path.dirname(path.realpath(__file__)), "../IO", "input")

    with open(input_file_path, 'r') as in_file:
        istream = " ".join(in_file.readlines())

    main(istream)