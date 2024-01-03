import os
import boto3
import tempfile
import pandas as pd
from rest_framework import status
from src.vector_db.get_item import get
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import AudioResponseSerializer
from rest_framework.parsers import MultiPartParser
from src.ai_integration.google_speech_api import get_transcription
from src.ai_integration.openai_tts_api import openai_text_to_speech_api


class AudioView(APIView):
    parser_classes = [MultiPartParser]

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        secret_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..", "other", "aws-info.csv")
        df = pd.read_csv(secret_file_path)

        row = df.iloc[0]

        self.region_name = row['region_name']
        self.aws_access_key_id = row['aws_access_key_id']
        self.aws_secret_access_key = row['aws_secret_access_key']
        self.bucket_name = "beanhubbucket"

    def post(self, request, format=None):
        if 'file' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client('s3', aws_access_key_id=self.aws_access_key_id,
                          aws_secret_access_key=self.aws_secret_access_key,
                          region_name=self.region_name)

        # Fetch the most recent .wav file from S3
        objects = s3.list_objects_v2(Bucket=self.bucket_name)['Contents']
        most_recent = max(objects, key=lambda x: x['LastModified'])


        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            s3.download_file(self.bucket_name, most_recent['Key'], temp_file.name)
            temp_file.close()

            _, transcription = get_transcription(temp_file.name)
        finally:
            os.remove(temp_file.name)

            # Process the transcription (assuming fixed response for now)
            res, success = get("cappuccino")
            price = res[0][-1] if success else -1.

            res_audio = openai_text_to_speech_api(f"The price of a cappuccino is {str(price)} dollars")
            res_audio_path = '/tmp/res_audio.wav'
            with open(res_audio_path, 'wb') as f:
                f.write(res_audio)

            s3.upload_file(res_audio_path, self.bucket_name, "result.wav")

            response_data = {
                'file': f"{self.bucket_name}/result.wav",
                'floating_point_number': price
            }

            serializer = AudioResponseSerializer(data=response_data)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
