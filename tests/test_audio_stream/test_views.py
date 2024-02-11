import os
import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.http import StreamingHttpResponse


@pytest.mark.skip(reason="Need to run with django test not pytest")
class AudioStreamTestCase(TestCase):
    def setUp(
            self
    ) -> None:
        super().setUp()
        self.mock_env = patch.dict(os.environ, {
            "REDIS_HOST": "test",
            "REDIS_PORT": "test",
            'RABBITMQ_HOST': "test",
        })
        self.mock_env.start()

        self.mock_pika_connection = patch('src.audio_stream.views.BlockingConnection').start()
        self.mock_pika_connection_parameters = patch('src.audio_stream.views.ConnectionParameters').start()

        self.mock_pika_channel = MagicMock()

        self.mock_pika_channel.queue_declare = MagicMock()
        self.mock_pika_channel.basic_consume = MagicMock()
        self.mock_pika_channel.start_consuming = MagicMock()
        self.mock_pika_channel.queue_delete = MagicMock()

        self.mock_pika_connection.start()
        self.mock_pika_connection_parameters.start()

        self.mock_conv_client = MagicMock()
        self.mock_conv_client.get = MagicMock()

        patch_conv = patch('src.audio_stream.views.AudioStreamView.connect_to_redis_temp_conversation_cache',
                           return_value=self.mock_conv_client)


        patch_conv.start()

    def tearDown(
            self
    ) -> None:
        patch.stopall()
        super().tearDown()

    def test_post_without_unique_id_throws_400_error_code(
            self
    ) -> None:
        # Arrange
        data = {
            # EMPTY
        }

        # Act
        response = self.client.post('/audio_stream/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_post_with_unique_id_returns_correct_response(
            self
    ) -> None:
        # Arrange
        data = {
            "unique_id": "foo"
        }

        # Act
        response = self.client.post('/audio_stream/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
