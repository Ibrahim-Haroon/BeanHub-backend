import json
import os
import uuid
import time
from pika import BlockingConnection, ConnectionParameters
import redis
import boto3
import logging
import tempfile
import threading
import psycopg2.pool
from os import getenv as env
from drf_yasg import openapi
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.views import APIView
from src.vector_db.get_deal import get_deal
from rest_framework.response import Response
from src.django_beanhub.settings import DEBUG
from drf_yasg.utils import swagger_auto_schema
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.conversational_ai import conv_ai
from src.vector_db.aws_database_auth import connection_string
from src.ai_integration.fine_tuned_nlp import split_order, make_order_report, human_requested, accepted_deal
from src.ai_integration.speech_to_text_api import google_cloud_speech_api, record_until_silence, return_as_wav

logging_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv()


class AudioView(APIView):

    def __init__(
            self, *args, **kwargs
    ):
        super().__init__(**kwargs)
        self.bucket_name = env('S3_BUCKET_NAME')
        self.conversation_cache = self.connect_to_redis_temp_conversation_cache()
        self.rabbitmq_connection = BlockingConnection(ConnectionParameters(env('RABBITMQ_HOST')))
        self.rabbitmq_channel = self.rabbitmq_connection.channel()
        self.deal_cache = self.connect_to_redis_temp_deal_cache()
        self.embedding_cache = self.connect_to_redis_embedding_cache()
        self.s3 = boto3.client('s3')
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())
        self.response_audio = None
        get_secret()

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
    def connect_to_redis_embedding_cache(

    ) -> redis.Redis:  # pragma: no cover
        while True:
            try:
                redis_client = redis.StrictRedis(host=env('REDIS_HOST'), port=env('REDIS_PORT'), db=1)
                logging.debug("Connected to embedding cache")
                return redis_client
            except redis.exceptions.ConnectionError:
                logging.debug("Failed to connect to Redis. Retrying in 5 seconds...")
                time.sleep(5)

    @staticmethod
    def connect_to_redis_temp_deal_cache(

    ) -> redis.Redis:  # pragma: no cover
        while True:
            try:
                redis_client = redis.StrictRedis(host=env('REDIS_HOST'), port=env('REDIS_PORT'), db=2)
                logging.debug("Connected to deal history")
                return redis_client
            except redis.exceptions.ConnectionError:
                logging.debug("Failed to connect to Redis. Retrying in 5 seconds...")
                time.sleep(5)

    @staticmethod
    def formatted_deal(
            order: dict
    ) -> list[dict] | Response:
        item_types = ['CoffeeItem', 'BeverageItem', 'FoodItem', 'BakeryItem']
        common_attributes = {'size': 'regular', 'temp': 'regular', 'add_ons': [], 'sweeteners': []}

        for item_type in ['CoffeeItem', 'BeverageItem']:
            if item_type in order:
                order[item_type].update(common_attributes)
                if item_type == 'CoffeeItem':
                    order[item_type]['milk_type'] = 'regular'

        if not any(item_type in order for item_type in item_types):
            return Response({'error': 'item_type not found'}, status=status.HTTP_400_BAD_REQUEST)

        return [order]

    @staticmethod
    def remove_duplicate_deal(
            deal: dict, orders: list[str]
    ) -> None:
        item_types = ['CoffeeItem', 'BeverageItem', 'FoodItem', 'BakeryItem']
        order_to_remove = None

        for item_type in item_types:
            if item_type in deal:
                item_name = deal[item_type]['item_name']
                for order in orders:
                    if item_name in order:
                        order_to_remove = order
                        break

        if order_to_remove:
            orders.remove(order_to_remove)

    def get_transcription(
            self, file_path: str
    ) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            start_time = time.time()
            self.s3.download_file(self.bucket_name, file_path, temp_file.name)
            logging.debug(f"download_file time: {time.time() - start_time}")

            temp_file.close()

            transcription = google_cloud_speech_api(temp_file.name)
        finally:
            os.remove(temp_file.name)

        return transcription

    def upload_file(
            self, unique_id: uuid.UUID = None
    ) -> None:
        res_audio_path = '/tmp/res_audio.wav'
        audio_write_time = time.time()
        with open(res_audio_path, 'wb') as f:
            while not self.response_audio:
                # wait 1 ms for response_audio to be set
                time.sleep(0.001)
            f.write(self.response_audio)
        logging.debug(f"audio_write time: {time.time() - audio_write_time}")

        upload_time = time.time()
        self.s3.upload_file(res_audio_path, self.bucket_name, f"result_{unique_id}.wav")
        logging.debug(f"upload_file time: {time.time() - upload_time}")

        return

    @swagger_auto_schema(
        operation_description=
        """
        Initial request from client. Expects file_path which is location of audio file (.wav) on s3 bucket. Creates a 
        unique id to manage conversation history and as security method in PATCH for verification. Then a transcription
        is generated and formatted. After a order report is generated along with a model report which contains more
        details such as allergins. Finally response is created with conversational AI, converted to speech (.wav), and
        written to s3 bucket.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'file_path': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='Path to the audio file on s3 bucket'),
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
            self, response, format=None
    ) -> Response:
        start_time = time.time()
        if 'file_path' not in response.data:
            return Response({'error': 'file_path not provided'}, status=status.HTTP_400_BAD_REQUEST)

        deal_object, deal_offered = None, False
        unique_id, _human_requested = uuid.uuid4(), False
        transcription = self.get_transcription(response.data['file_path'])

        if human_requested(transcription):
            _human_requested = True
            order_report, conv_history = self.transfer_control_to_human(unique_id, transcription)

            upload_thread = threading.Thread(target=self.upload_file, args=(unique_id,), daemon=True)
            upload_thread.start()
        else:
            order_report, conv_history, deal_object, deal_offered = self.post_normal_request(unique_id, transcription)

        response_data = {
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        self.conversation_cache.setex(name=f"conversation_history_{unique_id}",
                                      time=600,  # 10 minutes
                                      value=conv_history)

        deal_data = {
            "deal_offered": deal_offered,
            "deal_object": deal_object
        }
        self.deal_cache.setex(name=f"deal_history_{unique_id}",
                              time=600,  # 10 minutes
                              value=json.dumps(deal_data))

        if _human_requested:
            response_data.update({'file_path': f"result_{unique_id}.wav"})

        if response_data:
            logging.debug(f"total time: {time.time() - start_time}")
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{response_data}", status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description=
        """
        All updates from client. Expects file_path which is location of audio file (.wav) on s3 bucket and unique id to
        load conversation history. Then generates transcription and formatted. After a order report is generated along
        with a model report which contains more details such as allergins. Finally response is created with
        conversational AI (conversation history passed here), converted to speech (.wav), and written to s3 bucket.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'file_path': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='Path to the audio file on s3 bucket'),
                'unique_id': openapi.Schema(type=openapi.TYPE_STRING, description='UUID generated from initial POST'),
            },
        ),
        responses={
            200: 'OK',
            400: 'Bad Request',
            404: 'Not Found',
            500: 'Internal Error',
        },
    )
    def patch(
            self, response, format=None
    ) -> Response:
        start_time = time.time()
        if 'file_path' not in response.data or 'unique_id' not in response.data:
            return Response({'error': 'file_path or unique_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        unique_id, _human_requested = response.data['unique_id'], False
        transcription = self.get_transcription(response.data['file_path'])

        if accepted_deal(transcription):
            order_report, conv_history = self.process_and_format_deal(unique_id, transcription)
            self.deal_cache.append(key=f'deal_accepted_{unique_id}', value=json.dumps(True))
            if isinstance(order_report, Response):
                return order_report
        elif human_requested(transcription):
            _human_requested = True
            order_report, conv_history = self.transfer_control_to_human(unique_id, transcription)

            upload_thread = threading.Thread(target=self.upload_file, args=(unique_id,), daemon=True)
            upload_thread.start()
        else:
            try:
                offer_deal = bool(json.loads(self.deal_cache.get(
                    f'deal_accepted_{unique_id}')
                ))
            except TypeError:
                offer_deal = True

            order_report, conv_history = self.patch_normal_request(unique_id,
                                                                   transcription,
                                                                   offer_deal=offer_deal)

        self.conversation_cache.append(key=f"conversation_history_{unique_id}",
                                       value=conv_history)

        response_data = {
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        if _human_requested:
            response_data.update({'file_path': f"result_{unique_id}.wav"})

        if response_data:
            logging.debug(f"total time: {time.time() - start_time}")
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{response_data}", status=status.HTTP_400_BAD_REQUEST)

    def post_normal_request(
            self, unique_id: uuid.UUID, transcription: str, offer_deal: bool = True
    ) -> list[dict] and str and dict and bool:
        deal_object, deal, model_response = None, None, []
        formatted_transcription = split_order(transcription)
        order_report, model_report = make_order_report(formatted_transcription,
                                                       self.connection_pool,
                                                       self.embedding_cache,
                                                       aws_connected=True)

        if offer_deal and len(order_report) > 0:
            deal, deal_object, _ = get_deal(order_report[0],
                                            connection_pool=self.connection_pool,
                                            embedding_cache=self.embedding_cache)

        rabbitmq_thread = threading.Thread(target=self.rabbitmq_stream, args=(transcription,
                                                                              model_report,
                                                                              "",
                                                                              deal,
                                                                              unique_id,
                                                                              model_response), daemon=True)
        rabbitmq_thread.start()

        deal_offered = True
        conv_history = f"Customer: {transcription}\nModel: {''.join(model_response)}\n"

        return order_report, conv_history, deal_object, deal_offered

    def transfer_control_to_human(
            self, unique_id: uuid.UUID, transcription: str
    ) -> dict and str:
        human_response, response_transcription = record_until_silence()
        self.response_audio = return_as_wav(human_response)
        self.upload_file(unique_id)
        order_report = {
            'human_response': True
        }

        return order_report, f"Customer: {transcription}\nHuman: {response_transcription}\n"

    def process_and_format_deal(
            self, unique_id: uuid.UUID, transcription: str
    ) -> (list[dict] and str) or (Response and None):
        deal_data = self.deal_cache.get(f"deal_history_{unique_id}")
        deal_data = json.loads(deal_data)
        deal_report, order_report = self.formatted_deal(deal_data['deal_object']), None
        model_response = []

        if isinstance(deal_report, Response):
            return deal_report, None

        if len(transcription) > 4:
            formatted_transcription = split_order(transcription)
            # edge case to avoid double ordering of deal
            self.remove_duplicate_deal(deal_data['deal_object'], formatted_transcription)
            order_report, _ = make_order_report(formatted_transcription,
                                                self.connection_pool,
                                                self.embedding_cache,
                                                aws_connected=True)
            order_report.extend(deal_report)

        old_conv_history = self.conversation_cache.get(
            f"conversation_history_{unique_id} + 'CUSTOMER JUST ACCEPTED DEAL'"
        )
        rabbitmq_thread = threading.Thread(target=self.rabbitmq_stream, args=(transcription,
                                                                              str(order_report)
                                                                              if order_report
                                                                              else str(deal_report),
                                                                              old_conv_history,
                                                                              None,
                                                                              unique_id,
                                                                              model_response), daemon=True)
        rabbitmq_thread.start()

        conv_history = f"Customer: {transcription}\nModel: {''.join(model_response)}\n"

        self.deal_cache.delete(f"deal_history_{unique_id}")
        return order_report, conv_history

    def patch_normal_request(
            self, unique_id: uuid.UUID, transcription: str, offer_deal: bool = True
    ) -> list[dict] and str:
        deal_object, deal_offered, deal, model_response = None, False, None, []
        formatted_transcription = split_order(transcription)

        order_report, model_report = make_order_report(formatted_transcription,
                                                       self.connection_pool,
                                                       self.embedding_cache,
                                                       aws_connected=True)

        if offer_deal and len(order_report) > 0:
            deal, deal_object, _ = get_deal(order_report[0],
                                            connection_pool=self.connection_pool,
                                            embedding_cache=self.embedding_cache)

        old_conv_history = self.conversation_cache.get(f"conversation_history_{unique_id}")
        rabbitmq_thread = threading.Thread(target=self.rabbitmq_stream, args=(transcription,
                                                                              model_report,
                                                                              old_conv_history,
                                                                              deal,
                                                                              unique_id,
                                                                              model_response), daemon=True)
        rabbitmq_thread.start()

        deal_offered = True
        conv_history = f"Customer: {transcription}\nModel: {''.join(model_response)}\n"

        deal_data = {
            "deal_offered": deal_offered,
            "deal_object": deal_object
        }
        self.deal_cache.append(key=f"deal_history_{unique_id}",
                               value=json.dumps(deal_data))

        return order_report, conv_history

    def rabbitmq_stream(
            self, transcription: str, model_report, conversation_history: str, deal: str,
            unique_id: uuid.UUID, model_response: list[str]
    ) -> None:
        channel_queue = f"audio_stream_{unique_id}"

        self.rabbitmq_channel.queue_declare(queue=channel_queue)

        for model_response_chunk in conv_ai(transcription,
                                            model_report,
                                            conversation_history=conversation_history,
                                            deal=deal):
            if model_response_chunk:
                self.rabbitmq_channel.basic_publish(exchange='',
                                                    routing_key=channel_queue,
                                                    body=model_response_chunk)

                model_response.append(model_response_chunk)

        self.rabbitmq_channel.basic_publish(exchange='',
                                            routing_key=channel_queue,
                                            body='!COMPLETE!')
