import os
import json
import uuid
import boto3
import tempfile
from rest_framework import status
from src.vector_db.get_item import get_item
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import AudioResponseSerializer
from src.ai_integration.google_speech_api import get_transcription
from src.ai_integration.openai_tts_api import openai_text_to_speech_api


class AudioView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.bucket_name = os.environ['S3_BUCKET_NAME']


    def get_transcription(self, s3, file_path: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            s3.download_file(self.bucket_name, file_path, temp_file.name)
            temp_file.close()

            transcription = get_transcription(temp_file.name)
        finally:
            os.remove(temp_file.name)

        return transcription

    def upload_file(self, s3, transcription: str) -> uuid.UUID:
        res_audio = openai_text_to_speech_api(transcription)
        res_audio_path = '/tmp/res_audio.wav'
        with open(res_audio_path, 'wb') as f:
            f.write(res_audio)

        unique_id = uuid.uuid4()
        s3.upload_file(res_audio_path, self.bucket_name, f"result_{unique_id}.wav")

        return unique_id

    @staticmethod
    def get_order(transcription: str) -> json:
        order, _ = get_item(transcription)

        json_order = {
            "MenuItem": {
                "item_name": order[0][1],
                "item_quantity": order[0][2],
                "common_allergin": order[0][3],
                "num_calories": order[0][4],
                "price": order[0][5]
            }
        }

        return json_order

    def post(self, response, format=None):
        if 'file_path' not in response.data:
            return Response({'error': 'file not provided'}, status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client('s3')

        # transcription = self.get_transcription(s3, response.data['file_path'])

        temp_item = "cappuccino"
        order_details = self.get_order(temp_item)

        temp_transcription = f"The price of a cappuccino is {str(order_details['MenuItem']['price'])} dollars"
        unique_id = self.upload_file(s3, temp_transcription)

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_details
        }

        serializer = AudioResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # TODO: Implement PATCH method
    def PATCH(self, response, format=None):
        if 'unique_id' not in response.data:
            return Response({'error': 'unique_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client('s3')

        customer_order_file_path = "customer_order" + response.data['unique_id'] + ".wav"

        transcription = self.get_transcription(s3, response.data['file_path'])

        order_details = self.get_order(transcription)

        temp_transcription = f"The price of a {str(order_details['MenuItem']['item_name'])} is {str(order_details['MenuItem']['price'])} dollars"
        unique_id = self.upload_file(s3, temp_transcription)

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_details
        }

        serializer = AudioResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
