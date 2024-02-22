"""
This file is used to streaming audio bytes to client end over http
"""
import logging
import threading
from queue import Queue, Empty
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from django.http import StreamingHttpResponse
from pika.exceptions import ChannelError, ConnectionClosed
from src.django_beanhub.settings import DEBUG
from src.ai_integration.text_to_speech_api import openai_text_to_speech_api
from src.connection_manager import ConnectionManager

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')


class AudioStreamView(APIView):
    """
    This call implements the consume logic and streaming over http
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        connections = ConnectionManager.connect()
        #########################
        ## RABBITMQ CONNECTION ##
        self._rabbitmq_connection = connections.rabbitmq_connection()
        self._rabbitmq_channel = connections.rabbitmq_channel()
        #########################
        self.max_buffer_size: int = 15
        self.queue_timeout: int = 5

    def stream_audio(
            self, unique_id: str
    ) -> bytes or None:
        """
        @rtype: bytes or None
        @param unique_id: identifier to find correct channel to consume from
        @return: yields audio bytes
        """
        message_queue, text_buffer = Queue(), []
        threading.Thread(
            target=self.consume_messages,
            args=(unique_id, message_queue),
            daemon=True
        ).start()

        while True:
            try:
                audio_content: str = message_queue.get(timeout=self.queue_timeout)
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

    def consume_messages(
            self, unique_id: str, message_queue: Queue
    ) -> None:
        """
        @rtype: None
        @param unique_id: identifier to find correct channel
        @param message_queue: rabbitmq stream to consume from
        @return: Nothing
        """
        channel_queue = f"audio_stream_{unique_id}"
        self._rabbitmq_channel.queue_declare(queue=channel_queue, durable=True)

        # pylint: disable=W0613
        def callback(ch, method, properties, body):
            message_queue.put(body.decode('utf-8'))

        self._rabbitmq_channel.basic_consume(queue=channel_queue, on_message_callback=callback, auto_ack=True)
        self._rabbitmq_channel.start_consuming()

    def delete_rabbitmq_queue(
            self, unique_id: str
    ) -> None:
        """
        @rtype: None
        @param unique_id: identifier used to find correct channel queue to delete
        @return: None
        """
        channel_queue = f"audio_stream_{unique_id}"
        try:
            self._rabbitmq_channel.queue_delete(queue=channel_queue)
        except ChannelError as e:
            logging.debug("Failed to delete queue %s: ChannelError: %s", channel_queue, e)
        except ConnectionClosed as e:
            logging.debug("Failed to delete queue %s: ConnectionClosed: %s", channel_queue, e)

    @swagger_auto_schema(
        operation_description=
        """
        Stream audio bytes from Kafka topic which are produced
        from conversational AI model in audio_endpoint.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'unique_id': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='ID given from'
                                                        'audio_endpoint'
                                                        ' PATCH request. '
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
    # pylint: disable=C0116, W0613
    def get(
            self, request, *args, **kwargs
    ) -> StreamingHttpResponse:
        unique_id = request.query_params.get('unique_id')
        if not unique_id:
            return StreamingHttpResponse('Unique ID not provided', status=400)

        return StreamingHttpResponse(self.stream_audio(unique_id), content_type='audio/wav')
