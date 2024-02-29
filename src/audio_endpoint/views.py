"""
This file contains the AudioView class which is a subclass of APIView.
It is responsible for handling all requests and responses for the audio endpoint.
Details can be found on swagger documentation.
"""
import json
import uuid
import time
import logging
import threading
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from pika import BasicProperties
from other.decorators.time_log import time_log
from src.vector_db.get_deal import get_deal
from src.django_beanhub.settings import DEBUG
from src.audio_endpoint.utils.aws_s3 import get_transcription, upload_file
from src.audio_endpoint.utils.order_processing import remove_duplicate_deal, formatted_deal
from src.ai_integration.conversational_ai import conv_ai
from src.ai_integration.speech_to_text_api import record_until_silence, return_as_wav
from src.ai_integration.fine_tuned_nlp import split_transcription, make_order_report, human_requested, accepted_deal  # pylint: disable=C0301
from src.external_connections.connection_manager import ConnectionManager

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')


# pylint: disable=R0902, W0613
class AudioView(APIView):
    """
    This class is a subclass of APIView and is responsible for handling all requests and responses
    """

    def __init__(
            self, *args, **kwargs
    ):
        super().__init__(**kwargs)
        self.connections = ConnectionManager.connect()
        ####################
        ## AWS CONNECTION ##
        self.__s3 = self.connections.s3()
        self.__bucket_name = self.connections.bucket_name()
        ######################
        ## REDIS CONNECTION ##
        self.__conversation_cache = self.connections.redis_cache('conversation')
        self.__deal_cache = self.connections.redis_cache('deal')
        self.__embedding_cache = self.connections.redis_cache('embedding')
        ###########################
        ## POSTGRESQL CONNECTION ##
        self.__connection_pool = self.connections.connection_pool()
        ###########################

    @swagger_auto_schema(
        operation_description=
        """
        Initial request from client. Expects file_path which is location of audio file (.wav)
        on s3 bucket. Creates a unique id to manage conversation history and as security method
        in PATCH for verification. Then a transcription is generated and formatted. After a order
        report is generated along with a model report which contains more details such as allergins.
        Finally response is created with conversational AI, converted to speech (.wav), and written
        to s3 bucket.
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
    # pylint: disable=C0116
    @time_log
    def post(
            self, response
    ) -> Response:
        start_time = time.time()
        if 'file_path' not in response.data:
            return Response({'error': 'file_path not provided'}, status=status.HTTP_400_BAD_REQUEST)

        deal_object, deal_offered = None, False
        unique_id, _human_requested = uuid.uuid4(), False
        transcription = get_transcription(self.__s3, self.__bucket_name, response.data['file_path'])

        if human_requested(transcription):
            _human_requested = True
            order_report, conv_history = self.transfer_control_to_human(unique_id, transcription)
        else:
            res = self.post_normal_request(unique_id, transcription)
            order_report, conv_history, deal_object, deal_offered = res

        response_data = {
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        self.__conversation_cache.setex(name=f"conversation_history_{unique_id}",
                                        time=600,  # 10 minutes
                                        value=conv_history)

        deal_data = {
            "deal_offered": deal_offered,
            "deal_object": deal_object
        }
        self.__deal_cache.setex(name=f"deal_history_{unique_id}",
                                time=600,  # 10 minutes
                                value=json.dumps(deal_data))

        if _human_requested:
            response_data.update({'file_path': f"result_{unique_id}.wav"})

        if response_data:
            logging.debug("total time: %s", time.time() - start_time)
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(f"{transcription}\n{response_data}", status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description=
        """
        All updates from client. Expects file_path which is location of audio file (.wav)
        on s3 bucket and unique id to load conversation history. Then generates transcription
        and formatted. After a order report is generated along with a model report which contains
        more details such as allergins. Finally response is created with conversational AI
        (conversation history passed here), converted to speech (.wav), and written to s3 bucket.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'file_path': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='Path to the audio file on s3 bucket'),
                'unique_id': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='UUID generated from initial POST'),
            },
        ),
        responses={
            200: 'OK',
            400: 'Bad Request',
            404: 'Not Found',
            500: 'Internal Error',
        },
    )
    # pylint: disable=C0116
    @time_log
    def patch(
            self, response
    ) -> Response:
        if 'file_path' not in response.data or 'unique_id' not in response.data:
            return Response({'error': 'file_path or unique_id not provided'},
                            status=status.HTTP_400_BAD_REQUEST)

        unique_id, _human_requested = response.data['unique_id'], False
        transcription = get_transcription(self.__s3, self.__bucket_name, response.data['file_path'])

        if accepted_deal(transcription) and self.__deal_cache.get(f"deal_history_{unique_id}"):
            order_report, conv_history = self.process_and_format_deal(unique_id, transcription)
            self.__deal_cache.append(key=f'deal_accepted_{unique_id}', value=json.dumps(True))
            if isinstance(order_report, Response):
                return order_report
        elif human_requested(transcription):
            _human_requested = True
            order_report, conv_history = self.transfer_control_to_human(unique_id, transcription)
        else:
            try:
                offer_deal = not bool(json.loads(self.__deal_cache.get(
                    f'deal_accepted_{unique_id}')
                ))
            except TypeError:
                offer_deal = True

            order_report, conv_history = self.patch_normal_request(unique_id,
                                                                   transcription,
                                                                   offer_deal=offer_deal)

        self.__conversation_cache.append(key=f"conversation_history_{unique_id}",
                                         value=conv_history)

        response_data = {
            'unique_id': str(unique_id),
            'json_order': order_report
        }

        # delete each time since a new one will be offered per PATCH
        self.__deal_cache.delete(f"deal_history_{unique_id}")

        if _human_requested:
            response_data.update({'file_path': f"result_{unique_id}.wav"})

        if response_data:
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(f"{transcription}\n{response_data}", status=status.HTTP_400_BAD_REQUEST)

    def post_normal_request(
            self, unique_id: uuid.UUID, transcription: str, offer_deal: bool = True
    ) -> list[dict] and str and dict and bool:
        """
        @rtype: list[dict] and str and dict and bool
        @param unique_id: identifier to manage conversation history
        @param transcription: string of audio file
        @param offer_deal: flag to offer deal
        @return: order_report, conv_history, deal_object, deal_offered
        """
        deal_object, deal, model_response = None, None, []
        formatted_transcription = split_transcription(transcription)
        order_report, model_report = make_order_report(formatted_transcription,
                                                       self.__connection_pool,
                                                       self.__embedding_cache,
                                                       aws_connected=True)

        if offer_deal and len(order_report) > 0:  # pragma: no cover
            deal, deal_object, _ = get_deal(order_report[0],
                                            connection_pool=self.__connection_pool,
                                            embedding_cache=self.__embedding_cache)

        rabbitmq_thread = threading.Thread(target=self.rabbitmq_stream,
                                           args=(transcription,
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
        """
        @rtype: dict and str
        @param unique_id: identifier to manage conversation history
        @param transcription: string of audio file
        @return: order report and conversation history
        """
        human_response, response_transcription = record_until_silence()
        response_audio = return_as_wav(human_response)
        upload_file(self.__s3, self.__bucket_name, unique_id, response_audio)
        order_report = {
            'human_response': True
        }

        return order_report, f"Customer: {transcription}\nHuman: {response_transcription}\n"

    def process_and_format_deal(
            self, unique_id: uuid.UUID, transcription: str
    ) -> (list[dict] and str) or (Response and None):
        """
        @rtype: (list[dict] and str) or (Response and None)
        @param unique_id: identifier to manage conversation history
        @param transcription: string of audio file
        @return: order report and conversation history  or response and None
        """
        deal_data = self.__deal_cache.get(f"deal_history_{unique_id}")
        deal_data = json.loads(deal_data)
        deal_report, order_report = formatted_deal(deal_data['deal_object']), None
        model_response = []

        if isinstance(deal_report, Response):
            return deal_report, None

        if len(transcription) > 4:
            formatted_transcription = split_transcription(transcription)
            # edge case to avoid double ordering of deal
            remove_duplicate_deal(deal_data['deal_object'], formatted_transcription)
            order_report, _ = make_order_report(formatted_transcription,
                                                self.__connection_pool,
                                                self.__embedding_cache,
                                                aws_connected=True)
            order_report.extend(deal_report)

        old_conv_history = self.__conversation_cache.get(
            f"conversation_history_{unique_id} + 'CUSTOMER JUST ACCEPTED DEAL'"
        )
        rabbitmq_thread = threading.Thread(target=self.rabbitmq_stream,
                                           args=(transcription,
                                                 str(order_report)
                                                 if order_report
                                                 else str(deal_report),
                                                 old_conv_history,
                                                 None,
                                                 unique_id,
                                                 model_response), daemon=True)
        rabbitmq_thread.start()

        conv_history = f"Customer: {transcription}\nModel: {''.join(model_response)}\n"

        return order_report, conv_history

    def patch_normal_request(
            self, unique_id: uuid.UUID, transcription: str, offer_deal: bool = True
    ) -> list[dict] and str:
        """
        @rtype: list[dict] and str
        @param unique_id: identifier to manage conversation history
        @param transcription: string of audio file
        @param offer_deal: flag to offer deal
        @return: order_report and conversation history
        """
        deal_object, deal_offered, deal, model_response = None, False, None, []
        formatted_transcription = split_transcription(transcription)

        order_report, model_report = make_order_report(formatted_transcription,
                                                       self.__connection_pool,
                                                       self.__embedding_cache,
                                                       aws_connected=True)

        if offer_deal and len(order_report) > 0:
            deal, deal_object, _ = get_deal(order_report[0],
                                            connection_pool=self.__connection_pool,
                                            embedding_cache=self.__embedding_cache)

        old_conv_history = self.__conversation_cache.get(f"conversation_history_{unique_id}")
        rabbitmq_thread = threading.Thread(target=self.rabbitmq_stream,
                                           args=(transcription,
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
        self.__deal_cache.append(key=f"deal_history_{unique_id}",
                                 value=json.dumps(deal_data))

        return order_report, conv_history

    # pylint: disable=R0913
    def rabbitmq_stream(
            self, transcription: str, model_report: str, conversation_history: str, deal: str,
            unique_id: uuid.UUID, model_response: list[str]
    ) -> None:
        """
        @rtype: None
        @param transcription: string of audio file
        @param model_report: string of order report
        @param conversation_history: string of redis cache
        @param deal: most relevant deal
        @param unique_id: identifier to stream and conversation history
        @param model_response: pass by reference to build conversation history
        @return: None
        """
        channel_queue = f"audio_stream_{unique_id}"
        create_rabbitmq_connection = time.time()
        rabbitmq_connection = self.connections.rabbitmq_connection()
        logging.debug("Time to get rabbitmq connection in rabbitmq_stream: %s",
                      time.time() - create_rabbitmq_connection)
        rabbitmq_channel = rabbitmq_connection.channel()

        rabbitmq_channel.queue_declare(queue=channel_queue, durable=True)

        for model_response_chunk in conv_ai(transcription,
                                            model_report,
                                            conversation_history=conversation_history,
                                            deal=deal):

            if model_response_chunk:
                rabbitmq_channel.basic_publish(exchange='',
                                               routing_key=channel_queue,
                                               body=model_response_chunk,
                                               properties=BasicProperties(
                                                   delivery_mode=2,  # make message persistent
                                               ))
                logging.debug("Successfully published message to %s", channel_queue)

                model_response.append(model_response_chunk)

        rabbitmq_channel.basic_publish(exchange='',
                                       routing_key=channel_queue,
                                       body='!COMPLETE!')

        rabbitmq_channel.close()
        rabbitmq_connection.close()
