import os
import uuid
import redis
import boto3
import tempfile
from rest_framework import status
from rest_framework.views import APIView
from src.vector_db.get_item import get_item
from rest_framework.response import Response
from .serializers import AudioResponseSerializer
from src.ai_integration.conversational_ai import conv_ai, split_order, make_order_report
from src.ai_integration.google_speech_api import get_transcription
from src.ai_integration.openai_tts_api import openai_text_to_speech_api


class AudioView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.bucket_name = os.environ['S3_BUCKET_NAME']
        self.r = redis.Redis()
        self.s3 = boto3.client('s3')

    def get_transcription(self, file_path: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            self.s3.download_file(self.bucket_name, file_path, temp_file.name)
            temp_file.close()

            transcription = get_transcription(temp_file.name)

        finally:
            os.remove(temp_file.name)

        return transcription

    def upload_file(self, transcription: str, unique_id: uuid.UUID = None) -> uuid.UUID:
        res_audio = openai_text_to_speech_api(transcription)
        res_audio_path = '/tmp/res_audio.wav'
        with open(res_audio_path, 'wb') as f:
            f.write(res_audio)

        if not unique_id:
            unique_id = uuid.uuid4()
        self.s3.upload_file(res_audio_path, self.bucket_name, f"result_{unique_id}.wav")

        return unique_id

    def post(self, response, format=None):
        if 'file_path' not in response.data:
            return Response({'error': 'file not provided'}, status=status.HTTP_400_BAD_REQUEST)

        transcription = self.get_transcription(response.data['file_path'])
        formatted_transcription = split_order(transcription)

        order_report, order_report_str = make_order_report(formatted_transcription)

        model_response = conv_ai(transcription,
                                 order_report_str,
                                 conversation_history="")
        unique_id = self.upload_file(model_response)

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        self.r.setex(name=f"conversation_history_{unique_id}",
                     time=600, # 10 minutes
                     value=f"User: {transcription}\nModel: {model_response}\n")

        serializer = AudioResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(f"{serializer.data}", status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{order_report}\n{serializer.errors}", status=status.HTTP_400_BAD_REQUEST)

    def patch(self, response, format=None):
        if 'file_path' not in response.data or 'unique_id' not in response.data:
            return Response({'error': 'file_path or unique_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        unique_id = response.data['unique_id']

        transcription = self.get_transcription(response.data['file_path'])
        formatted_transcription = split_order(transcription)

        order_report, order_report_str = make_order_report(formatted_transcription)

        model_response = conv_ai(transcription,
                                 order_report_str,
                                 conversation_history=self.r.get(f"conversation_history_{unique_id}"))
        self.upload_file(model_response)

        self.r.append(f"conversation_history_{unique_id}",
                      f"User: \n{transcription}\nModel: {model_response}\n")

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        serializer = AudioResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
