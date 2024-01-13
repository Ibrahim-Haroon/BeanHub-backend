import os
import uuid
import redis
import time
import boto3
import logging
import tempfile
import threading
import psycopg2.pool
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import AudioResponseSerializer
from src.vector_db.aws_sdk_auth import get_secret
from src.vector_db.aws_database_auth import connection_string
from src.ai_integration.conversational_ai import conv_ai
from src.ai_integration.fine_tuned_nlp import split_order, make_order_report
from src.ai_integration.speech_to_text_api import google_cloud_speech_api
from src.ai_integration.text_to_speech_api import openai_text_to_speech_api

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


class AudioView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.bucket_name = os.environ['S3_BUCKET_NAME']
        self.r = redis.Redis()
        self.s3 = boto3.client('s3')
        get_secret()
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, connection_string())

    def get_transcription(self, file_path: str) -> str:
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

    def upload_file(self, transcription: str, unique_id: uuid.UUID = None) -> None:
        tts_time = time.time()
        res_audio = openai_text_to_speech_api(transcription)
        logging.info(f"tts time: {time.time() - tts_time}")

        res_audio_path = '/tmp/res_audio.wav'
        audio_write_time = time.time()
        with open(res_audio_path, 'wb') as f:
            f.write(res_audio)
        logging.info(f"audio_write time: {time.time() - audio_write_time}")

        upload_time = time.time()
        self.s3.upload_file(res_audio_path, self.bucket_name, f"result_{unique_id}.wav")
        logging.info(f"upload_file time: {time.time() - upload_time}")

        return

    def post(self, response, format=None):
        start_time = time.time()
        if 'file_path' not in response.data:
            return Response({'error': 'file not provided'}, status=status.HTTP_400_BAD_REQUEST)

        unique_id = uuid.uuid4()

        transcription = self.get_transcription(response.data['file_path'])
        formatted_transcription = split_order(transcription)

        order_report = make_order_report(formatted_transcription, self.connection_pool, aws_connected=True)

        model_response = conv_ai(transcription,
                                 str(order_report),
                                 conversation_history="")
        upload_thread = threading.Thread(target=self.upload_file, args=(model_response, unique_id))
        upload_thread.start()

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        self.r.setex(name=f"conversation_history_{unique_id}",
                     time=600,  # 10 minutes
                     value=f"User: {transcription}\nModel: {model_response}\n")

        serialize_time = time.time()
        serializer = AudioResponseSerializer(data=response_data)
        logging.info(f"serialize time: {time.time() - serialize_time}")
        if serializer.is_valid():
            upload_thread.join()
            return Response(f"total time:{time.time() - start_time}\n{serializer.data}", status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{order_report}\n{serializer.errors}", status=status.HTTP_400_BAD_REQUEST)

    def patch(self, response, format=None):

        if 'file_path' not in response.data or 'unique_id' not in response.data:
            return Response({'error': 'file_path or unique_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        unique_id = response.data['unique_id']

        transcription = self.get_transcription(response.data['file_path'])
        formatted_transcription = split_order(transcription)

        order_report = make_order_report(formatted_transcription, self.connection_pool, aws_connected=True)

        model_response = conv_ai(transcription,
                                 str(order_report),
                                 conversation_history=self.r.get(f"conversation_history_{unique_id}"))
        upload_thread = threading.Thread(target=self.upload_file, args=(model_response, unique_id))
        upload_thread.start()

        self.r.append(f"conversation_history_{unique_id}",
                      f"User: \n{transcription}\nModel: {model_response}\n")

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        serializer = AudioResponseSerializer(data=response_data)
        if serializer.is_valid():
            upload_thread.join()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{order_report}\n{serializer.errors}", status=status.HTTP_400_BAD_REQUEST)
