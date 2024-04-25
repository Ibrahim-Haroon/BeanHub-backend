"""
This module is used to convert text to speech using OpenAI's API
"""
# pylint: disable=R0801
from os import path
from os import getenv as env
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def openai_text_to_speech_api(
        text: str, api_key: str = None, audio_file_path: str = None
) -> bytes:
    """
    This function converts text to speech using OpenAI's API
    @param text: desired text to convert into audio
    @param api_key: key for OpenAI auth
    @param audio_file_path: file path to save if wanted
    @rtype: bytes
    @return audio
    """
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=env('OPENAI_API_KEY'))

    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text

    )

    if audio_file_path:
        response.stream_to_file(audio_file_path)

    return response.content


def main(
        text: str
) -> int:  # pragma: no cover
    """

    @param text: text from input file
    @return: 0 if successful
    """
    openai_text_to_speech_api(text)

    return 0


if __name__ == "__main__":  # pragma: no cover
    input_file_path = path.join(path.dirname(path.realpath(__file__)),
                                "../IO", "input")

    with open(input_file_path, 'r', encoding='utf-8') as in_file:
        ISTREAM = " ".join(in_file.readlines())

    main(ISTREAM)
