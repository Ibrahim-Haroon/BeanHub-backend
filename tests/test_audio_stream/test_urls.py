import os
import pytest
from django.test import TestCase
from mock import patch, MagicMock
from django.urls import resolve, reverse
from src.external_connections.connection_manager import ConnectionManager
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

        self.mock_connection_manager_instance = MagicMock()

        self.mock_connection_manager_instance.rabbitmq_connection.return_value = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.queue_declare = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.basic_consume = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.start_consuming = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.queue_delete = MagicMock()

        self.mock_connect = patch.object(
            ConnectionManager,
            'connect',
            return_value=self.mock_connection_manager_instance
        )
        self.mock_connect.start()

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
