import os
import pytest
from django.test import TestCase
from mock import patch, MagicMock, mock_open
from django.urls import resolve, reverse
from src.audio_stream.views import AudioStreamView


@pytest.mark.skip(reason="Need to run with django test not pytest")
class URLsTestCase(TestCase):
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
        unique_id = "foo-unique-id"
        url = reverse('audio-stream') + f'?unique_id={unique_id}'

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 200)
