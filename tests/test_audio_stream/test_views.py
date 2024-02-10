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

    def test_consume_message_with_valid_unique_id_returns_audio_stream(
            self
    ) -> None:
        # Arrange
        unique_id = "foo"

        data = {
            "unique_id": unique_id
        }

        self.mock_kafka_consumer.return_value.poll.side_effect = [
            MagicMock(key=lambda: unique_id.encode('utf-8'), value=lambda: 'Hello'.encode('utf-8')),
            MagicMock(key=lambda: unique_id.encode('utf-8'), value=lambda: '!COMPLETE!'.encode('utf-8'))
        ]

        # Act
        response = self.client.post('/audio_stream/', data, content_type='application/json')

        # Assert
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(response.status_code, 200)

    def test_consume_message_completion_signal_ends_stream(
            self
    ) -> None:
        # Arrange
        unique_id = "foo"

        data = {
            "unique_id": unique_id
        }

        self.mock_kafka_consumer.return_value.poll.side_effect = [
            MagicMock(key=lambda: unique_id.encode('utf-8'), value=lambda: 'Message 1'.encode('utf-8')),
            MagicMock(key=lambda: unique_id.encode('utf-8'), value=lambda: 'Message 2'.encode('utf-8')),
            MagicMock(key=lambda: unique_id.encode('utf-8'), value=lambda: '!COMPLETE!'.encode('utf-8')),
            None
        ]

        # Act
        response = self.client.post('/audio_stream/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_consume_message_no_start_offsets_subscribes_to_topic(
            self
    ) -> None:
        # Arrange
        unique_id = "new_id"
        self.mock_conv_client.get.return_value = None
        self.mock_kafka_consumer.return_value.poll.return_value = None

        data = {
            "unique_id": unique_id
        }


        # Act
        response = self.client.post('/audio_stream/', data, content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 200)


