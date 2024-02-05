import json
import os
import uuid
import time
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
from src.ai_integration.text_to_speech_api import openai_text_to_speech_api
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
                redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
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
                redis_client = redis.StrictRedis(host='localhost', port=6379, db=1)
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
                redis_client = redis.StrictRedis(host='localhost', port=6379, db=2)
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
        logging.debug(f"deal object in remove_duplicate_deal: {deal}")
        logging.debug(f"orders in remove_duplicate_deal: {orders}")
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

    def get_response_audio(
            self, transcription: str
    ) -> None:
        tts_time = time.time()
        self.response_audio = openai_text_to_speech_api(transcription)
        logging.debug(f"tts time: {time.time() - tts_time}")

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
        unique_id = uuid.uuid4()
        transcription = self.get_transcription(response.data['file_path'])

        if human_requested(transcription):
            order_report, conv_history = self.transfer_control_to_human(unique_id, transcription)
        else:
            order_report, conv_history, deal_object, deal_offered = self.post_normal_request(unique_id, transcription)

        upload_thread = threading.Thread(target=self.upload_file, args=(unique_id,))

        response_data = {
            'file_path': f"result_{unique_id}.wav",
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

        if response_data:
            logging.debug(f"total time: {time.time() - start_time}")
            upload_thread.start()
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

        unique_id = response.data['unique_id']
        transcription = self.get_transcription(response.data['file_path'])
        logging.debug("transcription: " + transcription)
        if accepted_deal(transcription):
            logging.debug(f"ACCEPTED DEAL")
            order_report, conv_history = self.process_and_format_deal(unique_id, transcription)
            self.deal_cache.append(key=f'deal_accepted_{unique_id}', value=json.dumps(True))
            if isinstance(order_report, Response):
                return order_report
        elif human_requested(transcription):
            logging.debug(f"HUMAN REQUESTED")
            order_report, conv_history = self.transfer_control_to_human(unique_id, transcription)
        else:
            logging.debug(f"NORMAL REQUEST")
            try:
                offer_deal = bool(json.loads(self.deal_cache.get(
                    f'deal_accepted_{unique_id}')
                ))
            except TypeError:
                offer_deal = True

            logging.debug(f"offer_deal: {offer_deal}")
            order_report, conv_history = self.patch_normal_request(unique_id,
                                                                   transcription,
                                                                   offer_deal=offer_deal)

        upload_thread = threading.Thread(target=self.upload_file, args=(unique_id,))

        self.conversation_cache.append(key=f"conversation_history_{unique_id}",
                                       value=conv_history)

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        if response_data:
            logging.debug(f"total time: {time.time() - start_time}")
            upload_thread.start()
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{response_data}", status=status.HTTP_400_BAD_REQUEST)

    def post_normal_request(
            self, unique_id: uuid.UUID, transcription: str, offer_deal: bool = True
    ) -> list[dict] and str and dict and bool:
        deal_object = None
        formatted_transcription = split_order(transcription)
        order_report, model_report = make_order_report(formatted_transcription,
                                                       self.connection_pool,
                                                       self.embedding_cache,
                                                       aws_connected=True)
        deal = None
        if offer_deal and len(order_report) > 0:
            deal, deal_object, _ = get_deal(order_report[0],
                                            connection_pool=self.connection_pool,
                                            embedding_cache=self.embedding_cache)
        model_response = conv_ai(transcription,
                                 model_report,
                                 conversation_history="",
                                 deal=deal)
        conv_history = f"Customer: {transcription}\nModel: {model_response}\n"
        deal_offered = True
        response_audio_thread = threading.Thread(target=self.get_response_audio, args=(model_response,))
        response_audio_thread.start()

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

        if isinstance(deal_report, Response):
            return deal_report, None

        if len(transcription) > 4:
            formatted_transcription = split_order(transcription)
            # edge case to avoid double ordering of deal
            logging.debug(f"formatted_transcription before remove_duplicate_deal: {formatted_transcription}")
            self.remove_duplicate_deal(deal_data['deal_object'], formatted_transcription)
            logging.debug(f"formatted_transcription after remove_duplicate_deal: {formatted_transcription}")
            order_report, model_report = make_order_report(formatted_transcription,
                                                           self.connection_pool,
                                                           self.embedding_cache,
                                                           aws_connected=True)
            order_report.extend(deal_report)

        model_response = conv_ai(transcription,
                                 str(order_report) if order_report else str(deal_report),
                                 conversation_history=str(self.conversation_cache.get(
                                     f"conversation_history_{unique_id}")) + "CUSTOMER JUST ACCEPTED DEAL")

        conv_history = f"Customer: {transcription}\nModel: {model_response}\n"
        response_audio_thread = threading.Thread(target=self.get_response_audio, args=(model_response,))
        response_audio_thread.start()

        self.deal_cache.delete(f"deal_history_{unique_id}")
        return order_report, conv_history

    def patch_normal_request(
            self, unique_id: uuid.UUID, transcription: str, offer_deal: bool = True
    ) -> list[dict] and str:
        deal_object, deal_offered = None, False
        formatted_transcription = split_order(transcription)

        order_report, model_report = make_order_report(formatted_transcription,
                                                       self.connection_pool,
                                                       self.embedding_cache,
                                                       aws_connected=True)
        deal = None
        if offer_deal and len(order_report) > 0:
            deal, deal_object, _ = get_deal(order_report[0],
                                            connection_pool=self.connection_pool,
                                            embedding_cache=self.embedding_cache)
        model_response = conv_ai(transcription,
                                 model_report,
                                 conversation_history=self.conversation_cache.get(
                                     f"conversation_history_{unique_id}"),
                                 deal=deal)
        deal_offered = True
        conv_history = f"Customer: {transcription}\nModel: {model_response}\n"
        response_audio_thread = threading.Thread(target=self.get_response_audio, args=(model_response,))
        response_audio_thread.start()

        deal_data = {
            "deal_offered": deal_offered,
            "deal_object": deal_object
        }
        self.deal_cache.append(key=f"deal_history_{unique_id}",
                               value=json.dumps(deal_data))

        return order_report, conv_history
