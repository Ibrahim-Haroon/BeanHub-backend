import os
import json
import uuid
import redis
import boto3
import tempfile
from rest_framework import status
from rest_framework.views import APIView
from src.vector_db.get_item import get_item
from rest_framework.response import Response
from .serializers import AudioResponseSerializer
from src.ai_integration.conversational_ai import conv_ai
from src.ai_integration.nlp_bert import ner_transformer
from src.ai_integration.google_speech_api import get_transcription
from src.ai_integration.openai_tts_api import openai_text_to_speech_api
import logging

logger = logging.getLogger(__name__)

from os import path
import sys

output_file_path = path.join(path.dirname(path.realpath(__file__)), "../IO", "output.txt")
sys.stdout = open(output_file_path, 'w')

class AudioView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.bucket_name = os.environ['S3_BUCKET_NAME']
        self.r = redis.Redis()

    def get_transcription(self, s3, file_path: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            s3.download_file(self.bucket_name, file_path, temp_file.name)
            temp_file.close()

            transcription = get_transcription(temp_file.name)
        finally:
            os.remove(temp_file.name)

        return transcription

    def upload_file(self, s3, transcription: str, unique_id: uuid.UUID = None) -> uuid.UUID:
        res_audio = openai_text_to_speech_api(transcription)
        res_audio_path = '/tmp/res_audio.wav'
        with open(res_audio_path, 'wb') as f:
            f.write(res_audio)

        if not unique_id:
            unique_id = uuid.uuid4()
        s3.upload_file(res_audio_path, self.bucket_name, f"result_{unique_id}.wav")

        return unique_id

    @staticmethod
    def coffee_order(order_report, order):
        db_order_details = None
        action = order_report[order]['action']
        ####
        logger.debug(f"action: {action}")
        print(f"coffee action: {action}")
        ####
        if action != 'question':
            db_order_details, _ = get_item(order_report[order]['coffee_type'])
        return {
            "MenuItem": {
                "item_name": db_order_details[0][1] if action != 'question' else "None",
                "quantity": order_report[order]['quantity'] if action != 'question' else 0,
                "price": db_order_details[0][5] if action != 'question' else 0.0,
                "temp": order_report[order]['temp'] if action != 'question' else "None",
                "add_ons": order_report[order]['add_ons'] if action != 'question' else "None",
                "milk_type": order_report[order]['milk_type'] if action != 'question' else "None",
                "sweeteners": order_report[order]['sweetener'] if action != 'question' else "None",
                "num_calories": db_order_details[0][4] if action != 'question' else "None",
                "cart_action": action
            }
        }

    @staticmethod
    def beverage_order(order_report, order):
        db_order_details = None
        action = order_report[order]['action']
        ####
        logger.debug(f"beverage action: {action}")
        print(f"beverage action: {action}")
        ####
        if action != 'question':
            db_order_details, _ = get_item(order_report[order]['beverage_type'])
        return {
            "MenuItem": {
                "item_name": db_order_details[0][1] if action != 'question' else "None",
                "quantity": order_report[order]['quantity'] if action != 'question' else 0,
                "price": db_order_details[0][5] if action != 'question' else 0.0,
                "temp": order_report[order]['temp'] if action != 'question' else "None",
                "add_ons": order_report[order]['add_ons'] if action != 'question' else "None",
                "sweeteners": order_report[order]['sweetener'] if action != 'question' else "None",
                "num_calories": db_order_details[0][4] if action != 'question' else "None",
                "cart_action": action
            }
        }

    @staticmethod
    def food_order(order_report, order):
        db_order_details = None
        action = order_report[order]['action']
        ####
        logger.debug(f"food action: {action}")
        print(f"food action: {action}")
        ####
        if action != 'question':
            db_order_details, _ = get_item(order_report[order]['food_item'])
        return {
            "MenuItem": {
                "item_name": db_order_details[0][1] if action != 'question' else "None",
                "quantity": order_report[order]['quantity'] if action != 'question' else 0,
                "price": db_order_details[0][5] if action != 'question' else 0.0,
                "num_calories": db_order_details[0][4] if action != 'question' else "None",
                "cart_action": action
            }
        }

    @staticmethod
    def bakery_order(order_report, order):
        db_order_details = None
        action = order_report[order]['action']
        ####
        logger.debug(f" bakery action: {action}")
        print(f"bakery action: {action}")
        ####
        if action != 'question':
            db_order_details, _ = get_item(order_report[order]['bakery_item'])
        return {
            "MenuItem": {
                "item_name": db_order_details[0][1] if action != 'question' else "None",
                "quantity": order_report[order]['quantity'] if action != 'question' else 0,
                "price": db_order_details[0][5] if action != 'question' else 0.0,
                "num_calories": db_order_details[0][4] if action != 'question' else "None",
                "cart_action": action
            }
        }

    def get_order(self, order_report) -> []:
        orders = []

        order_type_mapping = {
            'COFFEE_ORDER': self.coffee_order,
            'BEVERAGE_ORDER': self.beverage_order,
            'FOOD_ORDER': self.food_order,
            'BAKERY_ORDER': self.bakery_order
        }

        for order, meta in order_report.items():
            if order in order_type_mapping and meta != 'None':
                json_order = order_type_mapping[order](order_report, order)
                orders.append(json_order)

        return orders

    def post(self, response, format=None):
        if 'file_path' not in response.data:
            return Response({'error': 'file not provided'}, status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client('s3')


        # transcription = self.get_transcription(s3, response.data['file_path'])
        transcription = "Do you have 15 more glazed donuts?"
        ####
        logger.debug(f"transcription: {transcription}")
        print(f"transcription: {transcription}")
        ####
        tagged_sentence = ner_transformer(transcription)
        ####
        logger.debug(f"tagged_sentence: {tagged_sentence}")
        print(f"tagged_sentence: {tagged_sentence}")
        ####

        order_report = json.loads(conv_ai(transcription, tagged_sentence, conversation_history=""))
        ####
        logger.debug(f"order_report: {order_report}")
        print(f"order_report: {order_report}")
        ####
        order_details = self.get_order(order_report)
        ####
        logger.debug(f"order_details: {order_details}")
        print(f"order_details: {order_details}")
        ####

        model_response = order_report['CUSTOMER_RESPONSE']['response']
        ####
        logger.debug(f"model_response: {model_response}")
        print(f"model_response: {model_response}")
        ####
        unique_id = self.upload_file(s3, model_response if model_response else "Sorry, I didn't get that")

        response_data = {
            'file_path': f"result_{unique_id}.wav",
            'unique_id': str(unique_id),
            'json_order': order_details
        }

        self.r.setex(name=f"conversation_history_{unique_id}",
                     time=600, # 10 minutes
                     value=f"User: {transcription}\nModel: {model_response}\n")

        serializer = AudioResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(f"{serializer.data}", status=status.HTTP_200_OK)
        else:
            return Response(f"{transcription}\n{order_details}\n{serializer.errors}", status=status.HTTP_400_BAD_REQUEST)

    def patch(self, response, format=None):
        if 'file_path' not in response.data or 'unique_id' not in response.data:
            return Response({'error': 'file_path or unique_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client('s3')
        unique_id = response.data['unique_id']
        transcription = self.get_transcription(s3, response.data['file_path'])
        tagged_sentence = ner_transformer(transcription)


        order_report = json.loads(conv_ai(transcription,
                                   tagged_sentence,
                                   conversation_history=self.r.get(f"conversation_history_{unique_id}")))
        order_details = self.get_order(order_report)

        model_response = order_report['CUSTOMER_RESPONSE']['response']
        self.upload_file(s3, model_response if model_response else "Sorry, I didn't get that")

        self.r.append(f"conversation_history_{unique_id}",
                      f"User: \n{transcription}\nModel: {model_response}\n")

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
