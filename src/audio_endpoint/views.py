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
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from src.vector_db.aws_sdk_auth import get_secret
from src.ai_integration.conversational_ai import conv_ai
from src.vector_db.aws_database_auth import connection_string
from src.ai_integration.speech_to_text_api import google_cloud_speech_api
from src.ai_integration.text_to_speech_api import openai_text_to_speech_api
from src.ai_integration.fine_tuned_nlp import split_order, make_order_report

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


class AudioView(APIView):
    def __init__(
            self, *args, **kwargs
    ):
        super().__init__(**kwargs)
        self.bucket_name = env('S3_BUCKET_NAME')
        self.r = self.connect_to_redis_conversation_history()
        self.embedding_cache = self.connect_to_redis_embedding_cache()
        self.s3 = boto3.client('s3')
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())
        self.response_audio = None
        get_secret()

    @staticmethod
    def connect_to_redis_conversation_history(

    ) -> redis.Redis:
        while True:
            try:
                redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
                logging.info("Connected to conversation history")
                return redis_client
            except redis.exceptions.ConnectionError:
                logging.info("Failed to connect to Redis. Retrying in 5 seconds...")
                time.sleep(5)

    @staticmethod
    def connect_to_redis_embedding_cache(

    ) -> redis.Redis:
        while True:
            try:
                redis_client = redis.StrictRedis(host='localhost', port=6379, db=1)
                logging.info("Connected to embedding cache")
                return redis_client
            except redis.exceptions.ConnectionError:
                logging.info("Failed to connect to Redis. Retrying in 5 seconds...")
                time.sleep(5)

    def get_transcription(
            self, file_path: str
    ) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            start_time = time.time()
            self.s3.download_file(self.bucket_name, file_path, temp_file.name)
            logging.info(f"download_file time: {time.time() - start_time}")

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
        logging.info(f"tts time: {time.time() - tts_time}")

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
        logging.info(f"audio_write time: {time.time() - audio_write_time}")

        upload_time = time.time()
        self.s3.upload_file(res_audio_path, self.bucket_name, f"result_{unique_id}.wav")
        logging.info(f"upload_file time: {time.time() - upload_time}")

        return

    def post(
            self, response, format=None
    ):
        start_time = time.time()
        if 'file_path' not in response.data:
            return Response({'error': 'file_path not provided'}, status=status.HTTP_400_BAD_REQUEST)

        unique_id = uuid.uuid4()

        transcription = self.get_transcription(response.data['file_path'])
        formatted_transcription = split_order(transcription)
        order_report = make_order_report(formatted_transcription, self.connection_pool, self.embedding_cache, aws_connected=True)

        model_response = conv_ai(transcription,
                                 str(order_report),
                                 conversation_history="")
        response_audio_thread = threading.Thread(target=self.get_response_audio, args=(model_response,))
        response_audio_thread.start()
        upload_thread = threading.Thread(target=self.upload_file, args=(unique_id,))

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        self.r.setex(name=f"conversation_history_{unique_id}",
                     time=600,  # 10 minutes
                     value=f"User: {transcription}\nModel: {model_response}\n")

        if response_data:
            logging.info(f"total time: {time.time() - start_time}")
            upload_thread.start()
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{response_data}", status=status.HTTP_400_BAD_REQUEST)

    def patch(
            self, response, format=None
    ):
        start_time = time.time()
        if 'file_path' not in response.data or 'unique_id' not in response.data:
            return Response({'error': 'file_path or unique_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        unique_id = response.data['unique_id']

        transcription = self.get_transcription(response.data['file_path'])
        formatted_transcription = split_order(transcription)

        order_report = make_order_report(formatted_transcription, self.connection_pool, aws_connected=True)

        model_response = conv_ai(transcription,
                                 str(order_report),
                                 conversation_history=self.r.get(f"conversation_history_{unique_id}"))
        response_audio_thread = threading.Thread(target=self.get_response_audio, args=(model_response,))
        response_audio_thread.start()
        upload_thread = threading.Thread(target=self.upload_file, args=(unique_id,))

        self.r.append(f"conversation_history_{unique_id}",
                      f"User: \n{transcription}\nModel: {model_response}\n")

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        if response_data:
            logging.info(f"total time: {time.time() - start_time}")
            upload_thread.start()
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{response_data}", status=status.HTTP_400_BAD_REQUEST)
