import os
import json
import pytest
from typing import Final
from django.test import TestCase
from mock import patch, MagicMock, mock_open
from django.urls import resolve, reverse
from src.audio_endpoint.views import AudioView

speech_to_text_path: Final[str] = 'src.ai_integration.speech_to_text_api'
text_to_speech_path: Final[str] = 'src.ai_integration.text_to_speech_api'


@pytest.mark.skip(reason="Need to run with django test not pytest")
class URLsTestCase(TestCase):
    def setUp(
            self
    ) -> None:
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
            "DJANGO_INTERNAL_IPS": "test"
        })
        self.mock_env.start()

        self.mock_redis_temp_conv_cache = patch('src.audio_endpoint.views.redis.StrictRedis')
        mock_redis_conv_session_client = self.mock_redis_temp_conv_cache.start().return_value
        mock_redis_conv_session_client.setex = MagicMock()
        mock_redis_conv_session_client.append = MagicMock()

        self.mock_redis_temp_deal_cache = patch('src.audio_endpoint.views.redis.StrictRedis')
        mock_redis_deal_session_client = self.mock_redis_temp_deal_cache.start().return_value
        mock_redis_deal_session_client.setex = MagicMock()
        mock_redis_deal_session_client.append = MagicMock()
        mock_deal_data = {
            "deal_offered": 'foo',
            "deal_object": {}
        }
        mock_redis_deal_session_client.get = MagicMock(return_value=mock_deal_data)
        mock_redis_deal_session_client.flushdb = MagicMock()

        self.mock_redis_embedding_cache = patch('src.audio_endpoint.views.redis.StrictRedis')
        mock_redis_embedding_client = self.mock_redis_embedding_cache.start().return_value
        mock_redis_embedding_client.set = MagicMock()
        mock_redis_embedding_client.exists = MagicMock(return_value=False)
        mock_redis_embedding_client.get = MagicMock(return_value=json.dumps([0.1, 0.2, 0.3]))

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
                    {'alternatives': [{'transcript': 'test transcription'}]}
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

        self.mock_openai_response = patch('src.ai_integration.conversational_ai.get_openai_response')
        self.mock_openai_response.start().return_value.json.return_value = {
            "choices": [{"message": {"content": "mocked response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        mock_response = MagicMock()
        mock_response.content = b'mock response'
        self.mock_openai_tts = patch(text_to_speech_path + '.OpenAI')
        self.mock_openai_tts = self.mock_openai_tts.start()
        self.mock_openai_tts.return_value.audio.speech.create.return_value = mock_response

        self.mock_db_instance = patch('src.audio_endpoint.views.psycopg2.connect').start()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]
        self.mock_db_instance.return_value.cursor.return_value = mock_cursor

    def tearDown(
            self
    ) -> None:
        patch.stopall()
        super().tearDown()

    def test_audio_view_url_is_resolves_to_AudioView_class(
            self
    ) -> None:
        # Arrange
        url = reverse('audio-view')

        # Act

        # Assert
        self.assertEquals(resolve(url).func.view_class, AudioView)

    def test_audio_view_url_path(
            self
    ) -> None:
        # Arrange

        # Act

        # Assert
        self.assertEquals(reverse('audio-view'), '/audio_endpoint/')

    def test_audio_view_url_exists_at_desired_location_post_request(
            self
    ) -> None:
        # Arrange
        data = {
            'file_path': 'test.wav'
        }

        # Act
        response = self.client.post('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_audio_view_url_accessible_by_name_post_request(
            self
    ) -> None:
        # Arrange
        data = {
            'file_path': 'test.wav'
        }
        url = reverse('audio-view')

        # Act
        response = self.client.post(url, data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_audio_view_url_exists_at_desired_location_patch_request(
            self
    ) -> None:
        # Arrange
        data = {
            'file_path': 'test.wav',
            'unique_id': 'test'
        }

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_audio_view_url_accessible_by_name_patch_request(
            self
    ) -> None:
        # Arrange
        data = {
            'file_path': 'test.wav',
            'unique_id': 'test'
        }
        url = reverse('audio-view')

        # Act
        response = self.client.patch(url, data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
