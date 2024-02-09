from rest_framework.views import APIView
from django.http import StreamingHttpResponse
from confluent_kafka import Consumer, KafkaError
from src.ai_integration.text_to_speech_api import openai_text_to_speech_api


class AudioStreamView(APIView):

    def consume_message(
            self
    ):
        pass
