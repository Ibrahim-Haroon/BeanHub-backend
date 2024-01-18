import os
import pytest
from typing import Final
from django.test import TestCase
from mock import patch, MagicMock
from django.urls import resolve, reverse
from src.audio_endpoint.views import AudioView

speech_to_text_path: Final[str] = 'src.ai_integration.speech_to_text_api'
text_to_speech_path: Final[str] = 'src.ai_integration.text_to_speech_api'


@pytest.mark.skip(reason="Need to run with django test not pytest")
class URLsTestCase(TestCase):
    def setUp(self):
        self.mock_env = patch.dict(os.environ, {
            "S3_BUCKET_NAME": "test_bucket_name",
            "OPENAI_API_KEY": "test_api_key",
            "AWS_ACCESS_KEY_ID": "test_access_key_id",
            "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
            "AWS_DEFAULT_REGION": "us-east-1",
            "SECRET_NAME": "sneaky_bean",
            "RDS_DB_NAME": "test_db",
            "RDS_HOSTNAME": "test_host",
            "RDS_USERNAME": "test_user",
            "RDS_PASSWORD": "test_password",
            "RDS_PORT": "1234"
        })
        self.mock_env.start()

        self.mock_redis = patch('redis.Redis')
        self.mock_redis.start().return_value = MagicMock()

        self.mock_s3 = patch('src.audio_endpoint.views.boto3.client')
        self.mock_s3.start().return_value = MagicMock()

        self.mock_connection_string = patch('src.audio_endpoint.views.connection_string')
        self.mock_connection_string.start().return_value = MagicMock()

        self.mock_connection_pool = patch('pgvector.psycopg2.register_vector')
        self.mock_connection_pool.start().return_value = MagicMock()

        self.mock_boto3_session_client = patch('boto3.session.Session.client')
        self.mock_boto3_session_client.start().return_value = MagicMock()

        self.mock_google_cloud = patch(speech_to_text_path + '.speech.Recognizer')
        mock_recognizer_instance = MagicMock()
        self.mock_google_cloud.start().return_value = mock_recognizer_instance
        expected_transcription = "One black coffee"
        mock_recognizer_instance.recognize_google.return_value = expected_transcription

        self.mock_speech = patch(speech_to_text_path + '.speech.AudioFile')
        self.mock_speech.start().return_value = MagicMock()

        self.mock_openai_embedding_api = patch('src.vector_db.fill_vectordb.openai_embedding_api')
        self.mock_openai_embedding_api.start().return_value = MagicMock()
        self.mock_openai_response = patch('src.ai_integration.conversational_ai.get_openai_response')
        self.mock_openai_response.start().return_value.json.return_value = {
            "choices": [{"message": {"content": "mocked response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        mock_response = MagicMock()
        mock_response.content = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x00\x04\x00\x00\x00\x04\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00'
        self.mock_openai_tts = patch(text_to_speech_path + '.OpenAI')
        self.mock_openai_tts = self.mock_openai_tts.start()
        self.mock_openai_tts.return_value.audio.speech.create.return_value = mock_response

        self.mock_connection_string = patch('src.vector_db.aws_database_auth.connection_string')
        self.mock_connection_string.start().return_value = MagicMock()

        self.mock_connect = patch('src.vector_db.fill_vectordb.psycopg2.connect')
        self.mock_connect.start().return_value = MagicMock()

        self.mock_db_instance = patch('src.vector_db.contain_item.psycopg2.connect').start()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]
        self.mock_db_instance.return_value.cursor.return_value = mock_cursor

    def tearDown(self):
        patch.stopall()

    def test_audio_view_url_is_resolves_to_AudioView_class(self):
        # Arrange
        url = reverse('audio-view')

        # Act

        # Assert
        self.assertEquals(resolve(url).func.view_class, AudioView)

    def test_audio_view_url_path(self):
        # Arrange

        # Act

        # Assert
        self.assertEquals(reverse('audio-view'), '/audio_endpoint/')

    def test_audio_view_url_exists_at_desired_location_post_request(self):
        # Arrange
        data = {
            'file_path': 'test.wav'
        }

        # Act
        response = self.client.post('/audio_endpoint/', data)

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_audio_view_url_accessible_by_name_post_request(self):
        # Arrange
        data = {
            'file_path': 'test.wav'
        }
        url = reverse('audio-view')

        # Act
        response = self.client.post(url, data)

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_audio_view_url_exists_at_desired_location_patch_request(self):
        # Arrange
        data = {
            'file_path': 'test.wav',
            'unique_id': 'test'
        }

        # Act
        response = self.client.patch('/audio_endpoint/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_audio_view_url_accessible_by_name_patch_request(self):
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
