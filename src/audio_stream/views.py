import time
import uuid
import redis
import logging
import threading
from drf_yasg import openapi
from os import getenv as env
from queue import Queue, Empty
from dotenv import load_dotenv
from rest_framework.views import APIView
from src.django_beanhub.settings import DEBUG
from django.http import StreamingHttpResponse
from drf_yasg.utils import swagger_auto_schema
from pika import BlockingConnection, ConnectionParameters
from src.ai_integration.text_to_speech_api import openai_text_to_speech_api

logging_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


class AudioStreamView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_buffer_size = 15
        self.conversation_cache = self.connect_to_redis_temp_conversation_cache()

    @staticmethod
    def connect_to_redis_temp_conversation_cache(

    ) -> redis.Redis:  # pragma: no cover
        while True:
            try:
                redis_client = redis.StrictRedis(host=env('REDIS_HOST'), port=env('REDIS_PORT'), db=0)
                logging.debug("Connected to conversation history")
                return redis_client
            except redis.exceptions.ConnectionError:
                logging.debug("Failed to connect to Redis. Retrying in 5 seconds...")
                time.sleep(5)

    def stream_audio(
            self, unique_id
    ) -> bytes or None:
        message_queue, text_buffer = Queue(), []
        threading.Thread(target=self.consume_messages, args=(unique_id, message_queue), daemon=True).start()

        while True:
            try:
                audio_content: str = message_queue.get(timeout=10)
                if audio_content == '!COMPLETE!':
                    if text_buffer:
                        audio_bytes = openai_text_to_speech_api(''.join(text_buffer))
                        yield audio_bytes
                    break

                text_buffer.append(audio_content)

                if len(text_buffer) > self.max_buffer_size:
                    audio_bytes = openai_text_to_speech_api(''.join(text_buffer))
                    yield audio_bytes
                    text_buffer.clear()

            except Empty:
                break

        self.delete_rabbitmq_queue(unique_id)

    @staticmethod
    def consume_messages(
            unique_id: uuid.UUID, message_queue
    ) -> None:
        connection = BlockingConnection(ConnectionParameters(host=env('RABBITMQ_HOST')))
        channel = connection.channel()

        channel_queue = f"audio_stream_{unique_id}"
        channel.queue_declare(queue=channel_queue, durable=True)

        def callback(ch, method, properties, body):
            message_queue.put(body.decode('utf-8'))

        channel.basic_consume(queue=channel_queue, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    @staticmethod
    def delete_rabbitmq_queue(
            unique_id: uuid.UUID
    ) -> None:
        connection = BlockingConnection(ConnectionParameters(host=env('RABBITMQ_HOST')))
        channel = connection.channel()

        channel_queue = f"audio_stream_{unique_id}"
        try:
            channel.queue_delete(queue=channel_queue)
        except Exception as e:
            logging.debug(f"Failed to delete queue {channel_queue}: {e}")

    @swagger_auto_schema(
        operation_description=
        """
        Stream audio bytes from Kafka topic which are produced from conversational AI model in audio_endpoint.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'unique_id': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='ID given from audio_endpoint PATCH request. '
                                                        'Needed for verification.'),
            },
        ),
        responses={
            200: 'OK',
            400: 'Bad Request',
            404: 'Not Found',
            500: 'Internal Error',
        },
    )
    def post(
            self, response
    ) -> StreamingHttpResponse:
        if 'unique_id' not in response.data:
            return StreamingHttpResponse('Unique ID not provided', status=400)

        return StreamingHttpResponse(self.stream_audio(response.data['unique_id']), content_type='audio/wav')
