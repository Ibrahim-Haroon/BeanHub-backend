import os
from typing import Final
from django.test import TestCase
from unittest.mock import patch, MagicMock

speech_to_text_path: Final[str] = 'src.ai_integration.speech_to_text_api'


class AudioEndpointTestCase(TestCase):
    def setUp(self):
        self.mock_env = patch.dict(os.environ, {
            "S3_BUCKET_NAME": "test_bucket_name",
            "OPENAI_API_KEY": "test_api_key",
            "AWS_ACCESS_KEY_ID": "test_access_key_id",
            "AWS_SECRET_ACCESS_KEY": "test_secret_access_key",
            "AWS_DEFAULT_REGION": "us-east-1",
            "RDS_DB_NAME": "test_db",
            "RDS_HOSTNAME": "test_host",
            "RDS_USERNAME": "test_user",
            "RDS_PASSWORD": "test_password",
            "RDS_PORT": "1234"
        })
        self.mock_env.start()

        self.mock_boto3_session_client = patch('boto3.session.Session.client')
        self.mock_boto3_session_client.start().return_value = MagicMock()

        self.mock_google_cloud = patch(speech_to_text_path + '.speech.Recognizer')
        mock_recognizer_instance = MagicMock()
        self.mock_google_cloud.start().return_value = mock_recognizer_instance
        expected_transcription = "None"
        mock_recognizer_instance.recognize_google.return_value = expected_transcription

        self.mock_speech = patch(speech_to_text_path + '.speech.AudioFile')
        self.mock_speech.start().return_value = MagicMock()

        self.mock_redis = patch('redis.Redis')
        self.mock_redis_instance = MagicMock()
        self.mock_redis.start().return_value = self.mock_redis_instance

        self.mock_openai_embedding_api = patch('src.vector_db.fill_vectordb.openai_embedding_api').start()
        self.mock_connection_string = patch('src.vector_db.aws_database_auth.connection_string').start()
        self.mock_register_vector = patch('pgvector.psycopg2.register_vector').start()
        self.mock_connect = patch('src.vector_db.fill_vectordb.psycopg2.connect').start()
        self.mock_input = patch('builtins.input').start()

        self.mock_db_instance = patch('src.vector_db.contain_item.psycopg2.connect').start()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(7, 'test', 6, 'test', '(60,120)', 10.0)]
        self.mock_db_instance.return_value.cursor.return_value = mock_cursor

    def tearDown(self):
        self.mock_env.stop()
        self.mock_boto3_session_client.stop()
        self.mock_google_cloud.stop()
        self.mock_speech.stop()
        self.mock_redis.stop()
        self.mock_openai_embedding_api.stop()
        self.mock_connection_string.stop()
        self.mock_register_vector.stop()
        self.mock_connect.stop()
        self.mock_input.stop()
        self.mock_db_instance.stop()

    def test_post_without_file_path(self):
        response = self.client.post('/audio_endpoint/', {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'file_path not provided'})

    def test_post_with_file_path(self):
        response = self.client.post('/audio_endpoint/', {'file_path': 'test.wav'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('file_path' in response.json())
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

    def test_patch_without_file_path(self):
        response = self.client.patch('/audio_endpoint/', {'unique_id': 'test'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'file_path not provided'})

    def test_patch_without_unique_id(self):
        response = self.client.patch('/audio_endpoint/', {'file_path': 'test.wav'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'unique_id not provided'})

    def test_patch_with_file_path(self):
        response = self.client.post('/audio_endpoint/', {'file_path': 'test.wav'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('file_path' in response.json())
        self.assertTrue('unique_id' in response.json())
        self.assertTrue('json_order' in response.json())

