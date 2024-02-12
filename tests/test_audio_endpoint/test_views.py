import os
import json
import pytest
from typing import Final
from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open

speech_to_text_path: Final[str] = 'src.ai_integration.speech_to_text_api'
text_to_speech_path: Final[str] = 'src.ai_integration.text_to_speech_api'


@pytest.mark.skip(reason="Need to run with django test not pytest")
class AudioEndpointTestCase(TestCase):
    def setUp(
            self
    ) -> None:
        super().setUp()
        self.mock_env = patch.dict(os.environ, {
            "S3_BUCKET_NAME": "test_bucket_name",
            "OPENAI_API_KEY": "test_api_key",
            "DEEPGRAM_API_KEY": "test_api_key",
            "AWS_ACCESS_KEY_ID": "test_access_key_id",
            "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
            "AWS_DEFAULT_REGION": "us-east-1",
            "SECRET_NAME": "sneaky_bean",
            "RDS_DB_NAME": "test_db",
            "RDS_HOSTNAME": "test_host",
            "RDS_USERNAME": "test_user",
            "RDS_PASSWORD": "test_password",
            "RDS_PORT": "1234",
            "CODECOV_TOKEN": "codecov_token",
            "DJANGO_ALLOWED_HOSTS": "localhost 127.0.0.1 beanhub.ai",
            "DJANGO_SECRET_KEY": "test",
            "DJANGO_DEBUG_URL": "test",
            "DJANGO_ADMIN_URL": "test",
            "DJANGO_ROOT_URL": "test",
            "DJANGO_AUDIO_ENDPOINT_URL": "test",
            "DJANGO_AUDIO_STREAM_URL": "test",
            "DJANGO_SWAGGER_URL": "test",
            "DJANGO_REDOC_URL": "test",
            "APP_AUDIO_ENDPOINT_URL": "test",
            "DJANGO_DEBUG": "test",
            "DJANGO_CORS_ORIGIN_ALLOW_ALL": "test",
            "DJANGO_CORS_ALLOW_ALL_ORIGINS": "test",
            "DJANGO_ROOT_URLCONF": "test",
            "DJANGO_WSGI_APPLICATION": "test",
            "DJANGO_LANGUAGE_CODE": "test",
            "DJANGO_TIME_ZONE": "test",
            "DJANGO_USE_I18N": "test",
            "DJANGO_USE_TZ": "test",
            "DJANGO_STATIC_URL": "test",
            "DJANGO_DEFAULT_AUTO_FIELD": "test",
            "DJANGO_DEFAULT_FILE_STORAGE": "test",
            "DJANGO_INTERNAL_IPS": "test",
            "REDIS_HOST": "test",
            "REDIS_PORT": "test",
            'RABBITMQ_HOST': "test",
        })
        self.mock_env.start()

        self.mock_pika_connection = patch('src.audio_endpoint.views.BlockingConnection').start()
        self.mock_pika_connection_parameters = patch('src.audio_endpoint.views.ConnectionParameters').start()

        self.mock_pika_channel = MagicMock()

        self.mock_pika_channel.queue_declare = MagicMock()
        self.mock_pika_channel.basic_publish = MagicMock()

        self.mock_pika_connection.start()
        self.mock_pika_connection_parameters.start()

        self.mock_conv_client = MagicMock()
        self.mock_conv_client.setex = MagicMock()
        self.mock_conv_client.append = MagicMock()

        self.mock_embedding_client = MagicMock()
        self.mock_embedding_client.set = MagicMock()
        self.mock_embedding_client.exists = MagicMock(return_value=False)
        self.mock_embedding_client.get = MagicMock(return_value=json.dumps([0.1, 0.2, 0.3]))

        self.mock_deal_client = MagicMock()
        mock_deal_data = '{"deal_accepted": "foo", "deal_object": {}}'
        self.mock_deal_client.get = MagicMock(return_value=mock_deal_data)
        self.mock_deal_client.setex = MagicMock()
        self.mock_deal_client.append = MagicMock()
        self.mock_deal_client.flushdb = MagicMock()

        patch_conv = patch('src.audio_endpoint.views.AudioView.connect_to_redis_temp_conversation_cache',
                           return_value=self.mock_conv_client)
        patch_embedding = patch('src.audio_endpoint.views.AudioView.connect_to_redis_embedding_cache',
                                return_value=self.mock_embedding_client)
        patch_deal = patch('src.audio_endpoint.views.AudioView.connect_to_redis_temp_deal_cache',
                           return_value=self.mock_deal_client)

        patch_conv.start()
        patch_embedding.start()
        patch_deal.start()

        self.mock_s3 = patch('src.audio_endpoint.views.boto3.client')
        self.mock_s3.start().return_value = MagicMock()

        self.mock_connection_string = patch('src.audio_endpoint.views.connection_string')
        self.mock_connection_string.start().return_value = MagicMock()

        self.mock_boto3_session_client = patch('boto3.session.Session.client')
        self.mock_boto3_session_client.start().return_value = MagicMock()

        self.mock_google_cloud = patch(speech_to_text_path + '.speech.Recognizer')
        mock_recognizer_instance = MagicMock()
        self.mock_google_cloud.start().return_value = mock_recognizer_instance
        expected_transcription = "One black coffee"
        mock_recognizer_instance.recognize_google.return_value = expected_transcription

        self.mock_deepgram_file = patch('builtins.open', new_callable=mock_open, read_data='fake_deepgram_api_key')
        self.mock_deepgram_file.start()

        self.mock_deepgram_class = patch(speech_to_text_path + '.Deepgram')
        mock_deepgram_instance = MagicMock()
        self.mock_deepgram_class.start().return_value = mock_deepgram_instance
        nova_response = {
            'results': {
                'channels': [
                    {'alternatives': [{'transcript': 'this is a test'}]}
                ]
            }
        }
        mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response

        self.mock_speech = patch(speech_to_text_path + '.speech.AudioFile')
        self.mock_speech.start().return_value = MagicMock()

        self.mock_openai_embedding_api_get_item = patch('src.vector_db.get_item.openai_embedding_api')
        self.mock_openai_embedding_api_get_item.start().return_value = [0.1, 0.2, 0.3]

        self.mock_openai_embedding_api_get_deal = patch('src.vector_db.get_deal.openai_embedding_api')
        self.mock_openai_embedding_api_get_deal.start().return_value = [0.1, 0.2, 0.3]

        self.mock_openai_stream = patch('src.audio_endpoint.views.conv_ai')
        self.mock_openai_stream_gen = self.mock_openai_stream.start()
        self.mock_openai_stream_gen.side_effect = self.mock_streaming_response

        self.mock_db_instance = patch('src.audio_endpoint.views.psycopg2.connect').start()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]
        self.mock_db_instance.return_value.cursor.return_value = mock_cursor

    def tearDown(
            self
    ) -> None:
        patch.stopall()
        super().tearDown()

    @staticmethod
    def mock_streaming_response(*args, **kwargs):
        yield 'foo'

    def test_post_without_file_path_throws_400_error_code(
            self
    ) -> None:
        # Arrange
        data = {
            # EMPTY
        }

        # Act
        response = self.client.post('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'file_path not provided'})

    def test_post_with_file_path_returns_correct_response(
            self
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav"
        }

        # Act
        response = self.client.post('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    @patch('src.audio_endpoint.views.human_requested', return_value=True)
    @patch('src.audio_endpoint.views.record_until_silence', return_value=(
            "mocked_human_response",
            "mocked_response_transcription")
           )
    @patch('src.audio_endpoint.views.return_as_wav', return_value=b'mocked_audio_data')
    def test_post_returns_correct_response_when_human_requested_function_returns_true(
            self, mock_return_as_wav, mock_record_until_silence, mock_human_requested
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav"
        }

        # Act
        response = self.client.post('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('file_path' in response.json())
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    @patch('src.audio_endpoint.views.human_requested', return_value=False)
    def test_post_returns_correct_response_when_human_requested_returns_false(
            self, mock_human_requested
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav"
        }

        # Act
        response = self.client.post('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    @patch('src.audio_endpoint.views.human_requested', return_value=True)
    @patch('src.audio_endpoint.views.record_until_silence', return_value=(
            "mocked_human_response",
            "mocked_response_transcription")
           )
    @patch('src.audio_endpoint.views.return_as_wav', return_value=b'mocked_audio_data')
    def test_patch_sends_correct_response_when_human_requested_function_returns_true(
            self, mock_return_as_wav, mock_record_until_silence, mock_human_requested
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test"
        }

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('file_path' in response.json())
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    @patch('src.audio_endpoint.views.human_requested', return_value=False)
    def test_patch_sends_correct_response_when_human_requested_returns_false(
            self, mock_human_requested
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test"
        }

        # Act
        response = self.client.post('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    def test_patch_catches_request_without_file_path_and_throws_400_error(
            self
    ) -> None:
        # Arrange
        data = {
            "unique_id": "test"
        }

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'file_path or unique_id not provided'})

    def test_patch_catches_request_without_unique_id_and_throws_400_error(
            self
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav"
        }

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'file_path or unique_id not provided'})

    def test_patch_with_file_path_and_unique_id_sends_correct_response(
            self
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test"
        }

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    def test_patch_request_with_deal_cache_get_method_throwing_exception_correctly_assigns_offer_deal_and_returns_200(
            self
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test"
        }
        self.mock_deal_client.get = MagicMock(return_value=Exception)

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    @patch(speech_to_text_path + '.Deepgram')
    def test_patch_sends_successful_response_when_user_accepts_deal_and_nothing_else_and_deal_is_coffee_item(
            self, mock_deepgram
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test",
        }

        mock_deal_data = (
            '{'
            '    "deal_accepted": "foo",'
            '    "deal_object": {'
            '        "CoffeeItem": {'
            '            "item_name": "black coffee",'
            '            "quantity": [1],'
            '            "price": [2.0],'
            '            "cart_action": "insertion"'
            '        }'
            '    }'
            '}'
        )

        self.mock_deal_client.get = MagicMock(return_value=mock_deal_data)

        mock_deepgram_instance = MagicMock()
        mock_deepgram.return_value = mock_deepgram_instance
        nova_response = {
            'results': {
                'channels': [
                    {'alternatives': [{'transcript': 'yes'}]}
                ]
            }
        }
        mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    @patch(speech_to_text_path + '.Deepgram')
    def test_that_patch_returns_200_success_response_when_customer_accepts_deal_and_orders_another_item_in_same_request(
            self, mock_deepgram
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test",
        }

        mock_deal_data = (
            '{'
            '    "deal_accepted": "foo",'
            '    "deal_object": {'
            '        "CoffeeItem": {'
            '            "item_name": "latte",'
            '            "quantity": [1],'
            '            "price": [2.0],'
            '            "cart_action": "insertion"'
            '        }'
            '    }'
            '}'
        )

        self.mock_deal_client.get = MagicMock(return_value=mock_deal_data)

        mock_deepgram_instance = MagicMock()
        mock_deepgram.return_value = mock_deepgram_instance
        nova_response = {
            'results': {
                'channels': [
                    {'alternatives': [{'transcript': 'yes and one latte please'}]}
                ]
            }
        }
        mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    @patch(speech_to_text_path + '.Deepgram')
    def test_patch_sends_400_error_response_when_user_deal_invalid(
            self, mock_deepgram
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test",
        }

        mock_deepgram_instance = MagicMock()
        mock_deepgram.return_value = mock_deepgram_instance
        nova_response = {
            'results': {
                'channels': [
                    {'alternatives': [{'transcript': 'yes'}]}
                ]
            }
        }
        mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'item_type not found'})

    @patch(speech_to_text_path + '.Deepgram')
    def test_that_deal_cache_appends_deal_accepted_once_user_accepts_deal(
            self, mock_deepgram
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test",
        }

        mock_deepgram_instance = MagicMock()
        mock_deepgram.return_value = mock_deepgram_instance
        nova_response = {
            'results': {
                'channels': [
                    {'alternatives': [{'transcript': 'yes'}]}
                ]
            }
        }
        mock_deepgram_instance.transcription.sync_prerecorded.return_value = nova_response

        # Act
        self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        assert bool(json.loads(self.mock_deal_client.get(f'deal_accepted_{data["unique_id"]}'))) is True, \
            "deal_accepted not appended to cache"

    def test_that_patch_normal_request_param_offer_deal_equals_false_when_deal_has_been_accepted(
            self
    ) -> None:
        # Arrange
        data = {
            "file_path": "test.wav",
            "unique_id": "test",
        }

        self.mock_deal_client.get = MagicMock(return_value=json.dumps(False))

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())
