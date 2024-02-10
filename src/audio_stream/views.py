import time
import json
import redis
import logging
from os import getenv as env
from dotenv import load_dotenv
from rest_framework.views import APIView
from src.django_beanhub.settings import DEBUG
from django.http import StreamingHttpResponse
from confluent_kafka import Consumer, KafkaError, TopicPartition, OFFSET_BEGINNING
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

    @staticmethod
    def on_assign(consumer, partitions):
        for partition in partitions:
            partition.offset = OFFSET_BEGINNING
        consumer.assign(partitions)

    def get_start_offsets(self, unique_id):
        offset_data = self.conversation_cache.get(f"kafka_message_offset_{unique_id}")
        if not offset_data:
            return []

        records = json.loads(offset_data.decode('utf-8'))

        return [TopicPartition(record['topic'], record['partition'], record['offset'] + 1) for record in records]

    def consume_message(
            self, unique_id
    ) -> bytes or None:
        consumer = Consumer({
            'bootstrap.servers': env('KAFKA_BROKER_URL'),
            'group.id': 'audio_stream_group',
            'auto.offset.reset': 'earliest'
        })

        kafka_topic = env('KAFKA_TOPIC')
        start_offsets = self.get_start_offsets(unique_id)

        if start_offsets:
            logging.debug(f"Assigning start offsets: {start_offsets}")
            consumer.assign(start_offsets)
        else:
            logging.debug("No start offsets found. Subscribing to topic...")
            consumer.subscribe([kafka_topic], on_assign=self.on_assign)

        text_buffer = []

        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    logging.debug("No message received")
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logging.debug(f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                        continue
                    elif msg.error().code() != KafkaError.NO_ERROR:
                        logging.debug(f"Error: {msg.error()}")
                        break

                if msg.key() is None or msg.value() is None:
                    logging.debug("key or value empty. Skipping...")
                    continue

                if msg.key().decode('utf-8') == unique_id:
                    text = msg.value().decode('utf-8')
                    logging.debug(f"Received message: {text}")
                    if text == '!COMPLETE!':
                        logging.debug("Received completion message.")
                        if text_buffer:
                            logging.debug("Buffer not empty. Generating audio...")
                            audio_bytes = openai_text_to_speech_api(''.join(text_buffer))
                            yield audio_bytes
                        break

                    text_buffer.append(text)
                    logging.debug("Appended to buffer")

                    if len(text_buffer) >= self.max_buffer_size:
                        logging.debug("Buffer full. Generating audio...")
                        audio_bytes = openai_text_to_speech_api(''.join(text_buffer))
                        yield audio_bytes
                        text_buffer.clear()
        finally:
            consumer.close()
            logging.debug("Consumer closed")

    def get(
            self, request, *args, **kwargs
    ) -> StreamingHttpResponse:
        if 'unique_id' not in request.data:
            return StreamingHttpResponse('Unique ID not provided', status=400)

        return StreamingHttpResponse(self.consume_message(request.data['unique_id']), content_type='audio/wav')
