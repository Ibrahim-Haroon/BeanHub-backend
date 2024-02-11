import os
import json
import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.http import StreamingHttpResponse
from queue import Empty


@pytest.mark.skip(reason="Need to run with django test not pytest")
class AudioStreamTestCase(TestCase):
    def setUp(
            self
    ) -> None:
        super().setUp()
        self.mock_env = patch.dict(os.environ, {
            "OPENAI_API_KEY": "test_api_key",
            "REDIS_HOST": "test",
            "REDIS_PORT": "test",
            'RABBITMQ_HOST': "test"
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

        self.mock_openai_tts = patch('src.audio_stream.views.openai_text_to_speech_api')
        self.mock_openai_tts.start().return_value = b'test'

        self.mock_queue = patch('queue.Queue')
        self.mock_queue.start().get.return_value = b'test'

    def tearDown(
            self
    ) -> None:
        patch.stopall()
        super().tearDown()

    def test_get_without_unique_id_throws_400_error_code(
            self
    ) -> None:
        # Arrange
        url = reverse('audio-stream') + f'?unique_id='

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_get_with_unique_id_returns_correct_response(self) -> None:
        # Arrange
        unique_id = "foo-unique-id"
        url = reverse('audio-stream') + f'?unique_id={unique_id}'

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 200)
