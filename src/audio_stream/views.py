import logging
from os import getenv as env
from dotenv import load_dotenv
from rest_framework.views import APIView
from src.django_beanhub.settings import DEBUG
from django.http import StreamingHttpResponse
from confluent_kafka import Consumer, KafkaError
from src.ai_integration.text_to_speech_api import openai_text_to_speech_api

logging_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


class AudioStreamView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.consumer = Consumer({
            'bootstrap.servers': env('KAFKA_BROKER_URL'),
            'group.id': 'audio_stream_group',
            'auto.offset.reset': 'earliest'
        })
        self.kafka_topic = env('KAFKA_TOPIC')
        self.consumer.subscribe([self.kafka_topic])

    def consume_message(
            self, unique_id
    ) -> bytes or None:
        text_buffer = []
        word_count_target = 4

        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                elif msg.error().code() != KafkaError.NO_ERROR:
                    logging.debug(f"Error: {msg.error()}")
                    break

            if msg.value() is None:
                continue

            if msg.key().decode('utf-8') == unique_id:
                text = msg.value().decode('utf-8')

                # Check for termination signal
                if text == '!COMPLETE!':
                    if text_buffer:
                        audio_bytes = openai_text_to_speech_api(''.join(text_buffer))
                        yield audio_bytes
                    break

                text_buffer.append(text)

                if len(text_buffer) >= word_count_target:
                    audio_bytes = openai_text_to_speech_api(''.join(text_buffer))
                    yield audio_bytes
                    text_buffer.clear()

    def get(
            self, request, *args, **kwargs
    ) -> StreamingHttpResponse:
        if 'unique_id' not in request.data:
            return StreamingHttpResponse('Unique ID not provided', status=400)

        return StreamingHttpResponse(self.consume_message(request.data['unique_id']), content_type='audio/wav')
