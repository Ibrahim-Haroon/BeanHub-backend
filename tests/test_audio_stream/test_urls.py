import os
import json
import pytest
from typing import Final
from django.test import TestCase
from mock import patch, MagicMock, mock_open
from django.urls import resolve, reverse
from src.audio_stream.views import AudioStreamView

speech_to_text_path: Final[str] = 'src.ai_integration.speech_to_text_api'
text_to_speech_path: Final[str] = 'src.ai_integration.text_to_speech_api'


@pytest.mark.skip(reason="Need to run with django test not pytest")
class URLsTestCase(TestCase):
    def setUp(
            self
    ) -> None:
        super().setUp()
        self.mock_env = patch.dict(os.environ, {
            "REDIS_HOST": "test",
            "REDIS_PORT": "test",
            'KAFKA_BROKER_URL': "127.0.0.2",
            'KAFKA_TOPIC': "test"
        })
        self.mock_env.start()

        self.mock_kafka_consumer_class = patch('confluent_kafka.Consumer', autospec=True)
        self.mock_kafka_consumer = self.mock_kafka_consumer_class.start()
        self.mock_kafka_consumer.return_value.assign = MagicMock()
        self.mock_kafka_consumer.return_value.subscribe = MagicMock()
        self.mock_kafka_consumer.return_value.poll = MagicMock()
        self.mock_kafka_consumer.return_value.close = MagicMock()

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

    def test_audio_stream_url_is_resolves_to_AudioStreamView_class(
            self
    ) -> None:
        # Arrange
        url = reverse('audio-stream')

        # Act

        # Assert
        self.assertEquals(resolve(url).func.view_class, AudioStreamView)

    def test_audio_stream_url_path(
            self
    ) -> None:
        # Arrange

        # Act

        # Assert
        self.assertEquals(reverse('audio-stream'), '/audio_stream/')

    def test_audio_stream_url_exists_at_desired_location_get_request(
            self
    ) -> None:
        # Arrange
        data = {
            'unique_id': 'foo_id'
        }

        # Act
        response = self.client.post('/audio_stream/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_audio_stream_url_accessible_by_name_get_request(
            self
    ) -> None:
        # Arrange
        data = {
            'unique_id': 'foo_id'
        }
        url = reverse('audio-stream')

        # Act
        response = self.client.post(url, data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)
