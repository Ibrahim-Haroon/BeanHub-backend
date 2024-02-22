import os
import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock, ANY
from django.urls import reverse
from django.http import StreamingHttpResponse
import queue
from pika.exceptions import ChannelError, ConnectionClosed
from src.connection_manager import ConnectionManager
from src.audio_stream.views import AudioStreamView


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

        self.mock_connection_manager_instance = MagicMock()

        self.mock_connection_manager_instance.rabbitmq_connection.return_value = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.queue_declare = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.basic_consume = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.start_consuming = MagicMock()
        self.mock_connection_manager_instance.rabbitmq_channel.queue_delete = MagicMock()

        self.mock_connect = patch.object(ConnectionManager, 'connect',
                                         return_value=self.mock_connection_manager_instance)
        self.mock_connect.start()

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

    def test_stream_audio_returns_correct_response(
            self
    ) -> None:
        # Arrange
        unique_id = "foo-unique-id"
        url = reverse('audio-stream') + f'?unique_id={unique_id}'
        mock_queue = MagicMock(spec=queue.Queue)
        mock_queue.get.side_effect = 'test'

        patch('src.audio_stream.views.queue.Queue', return_value=mock_queue)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'audio/wav')

    @patch('src.audio_stream.views.threading.Thread')
    @patch('src.audio_stream.views.openai_text_to_speech_api')
    def test_stream_audio_yields_correct_audio_bytes(
            self, mock_tts_api, mock_thread
    ) -> None:
        # Arrange
        view_instance = AudioStreamView()
        unique_id = "test-id"
        mock_tts_api.return_value = b'audio-bytes'
        messages = ['hello', 'world', '!COMPLETE!']

        with patch('src.audio_stream.views.Queue') as mock_queue_class:
            mock_queue = queue.Queue()
            for msg in messages:
                mock_queue.put(msg)
            mock_queue_class.return_value = mock_queue

            # Act
            audio_stream_generator = view_instance.stream_audio(unique_id)
            audio_bytes = list(audio_stream_generator)

            # Assert
            mock_tts_api.assert_called_with('helloworld')
            self.assertEqual(audio_bytes, [b'audio-bytes'])
            mock_thread.assert_called()

    @patch('src.audio_stream.views.threading.Thread')
    @patch('src.audio_stream.views.openai_text_to_speech_api')
    def test_stream_audio_completes_on_complete_message(
            self, mock_tts_api, mock_thread
    ) -> None:
        # Arrange
        view_instance = AudioStreamView().__new__(AudioStreamView)
        view_instance.max_buffer_size = 0
        view_instance.queue_timeout = 1
        view_instance._rabbitmq_channel = MagicMock()
        view_instance._rabbitmq_channel.queue_delete = MagicMock()

        unique_id = "test-id-complete"
        mock_tts_api.return_value = b'final-audio-bytes'
        messages = ['final', '!COMPLETE!']

        with patch('src.audio_stream.views.Queue') as mock_queue_class:
            mock_queue = queue.Queue()
            for msg in messages:
                mock_queue.put(msg)
            mock_queue_class.return_value = mock_queue

            # Act
            audio_stream_generator = view_instance.stream_audio(unique_id)
            audio_bytes = list(audio_stream_generator)

            # Assert
            mock_tts_api.assert_called_with('final')
            self.assertEqual(audio_bytes, [b'final-audio-bytes'])
            mock_thread.assert_called()

    @patch('src.audio_stream.views.threading.Thread')
    @patch('src.audio_stream.views.openai_text_to_speech_api')
    def test_stream_audio_completes_on_empty_queue(
            self, mock_tts_api, mock_thread
    ) -> None:
        # Arrange
        view_instance = AudioStreamView().__new__(AudioStreamView)
        view_instance.max_buffer_size = 0
        view_instance.queue_timeout = 0
        view_instance._rabbitmq_channel = MagicMock()
        view_instance._rabbitmq_channel.queue_delete = MagicMock()

        unique_id = "test-id-complete"
        mock_tts_api.return_value = b'final-audio-bytes'
        messages = []

        with patch('src.audio_stream.views.Queue') as mock_queue_class:
            mock_queue = queue.Queue()
            for msg in messages:
                mock_queue.put(msg)
            mock_queue_class.return_value = mock_queue

            # Act
            audio_stream_generator = view_instance.stream_audio(unique_id)
            audio_bytes = list(audio_stream_generator)

            # Assert
            self.assertEqual(audio_bytes, [])

    # def test_consume_messages_puts_received_messages_into_queue(
    #         self
    # ) -> None:
    #     # Arrange
    #     view_instance = AudioStreamView().__new__(AudioStreamView)
    #     view_instance.max_buffer_size = 15
    #     view_instance.queue_timeout = 5
    #     view_instance._rabbitmq_channel = MagicMock()
    #     view_instance._rabbitmq_connection = MagicMock()
    #
    #     unique_id = "test-id"
    #     test_messages = [b'First message', b'Second message', b'Third message']
    #
    #     mock_channel = MagicMock()
    #     view_instance._rabbitmq_connection.return_value.channel.return_value = mock_channel
    #
    #     def on_message_callback_simulator(
    #             msg_queue, on_message_callback, auto_ack
    #     ) -> None:
    #         for message in test_messages:
    #             on_message_callback(None, None, None, message)
    #
    #     mock_channel.basic_consume.side_effect = on_message_callback_simulator
    #
    #     message_queue = queue.Queue()
    #
    #     # Act
    #     view_instance.consume_messages(unique_id, message_queue)
    #
    #     # Assert
    #     self.assertEqual(message_queue.qsize(), len(test_messages))
    #     for msg in test_messages:
    #         self.assertEqual(message_queue.get(), msg.decode('utf-8'))
    #
    #     view_instance._rabbitmq_connection.assert_called_once_with(view_instance._rabbitmq_connection(host=ANY))
    #     mock_channel.queue_declare.assert_called_once_with(queue=f"audio_stream_{unique_id}", durable=True)
    #     mock_channel.basic_consume.assert_called_once()
    #     mock_channel.start_consuming.assert_called_once()

    def test_consume_messages_puts_received_messages_into_queue(self):
        # Arrange
        view_instance = AudioStreamView().__new__(AudioStreamView)
        view_instance.max_buffer_size = 15
        view_instance.queue_timeout = 5
        view_instance._rabbitmq_channel = MagicMock()
        view_instance._rabbitmq_connection = MagicMock()

        unique_id = "test-id"
        test_messages = [b'First message', b'Second message', b'Third message']

        def on_message_callback(
                ch, method, properties, body
        ) -> None:
            message_queue.put(body.decode('utf-8'))

        view_instance._rabbitmq_channel.basic_consume.side_effect = lambda queue, on_message_callback, auto_ack: [
            on_message_callback(None, None, None, _msg_) for _msg_ in test_messages]

        view_instance._rabbitmq_channel.start_consuming.side_effect = lambda: None  # Prevent actual consuming

        message_queue = queue.Queue()

        # Act
        view_instance.consume_messages(unique_id, message_queue)

        # Assert
        self.assertEqual(message_queue.qsize(), len(test_messages))
        for msg in test_messages:
            self.assertEqual(message_queue.get(), msg.decode('utf-8'))

        view_instance._rabbitmq_channel.queue_declare.assert_called_once_with(
            queue=f"audio_stream_{unique_id}",
            durable=True
        )
        view_instance._rabbitmq_channel.basic_consume.assert_called()

    @patch('src.audio_stream.views.logging.debug')
    def test_delete_rabbitmq_queue_successfully(self, mock_logging):
        # Arrange
        unique_id = "test-id"
        view_instance = AudioStreamView().__new__(AudioStreamView)
        view_instance.max_buffer_size = 15
        view_instance.queue_timeout = 5
        view_instance._rabbitmq_channel = MagicMock()

        # Act
        view_instance.delete_rabbitmq_queue(unique_id)

        # Assert
        view_instance._rabbitmq_channel.queue_delete.assert_called_once_with(queue=f"audio_stream_{unique_id}")
        mock_logging.assert_not_called()  # Ensure no error logging on successful deletion

    @patch('src.audio_stream.views.logging.debug')
    def test_delete_rabbitmq_queue_handles_channel_error_exception(self, mock_logging):
        # Arrange
        unique_id = "test-id"
        view_instance = AudioStreamView().__new__(AudioStreamView)
        view_instance.max_buffer_size = 15
        view_instance.queue_timeout = 5
        view_instance._rabbitmq_channel = MagicMock()
        view_instance._rabbitmq_channel.queue_delete.side_effect = ChannelError("test")

        # Act
        view_instance.delete_rabbitmq_queue(unique_id)

        # Assert
        view_instance._rabbitmq_channel.queue_delete.assert_called_once_with(queue=f"audio_stream_{unique_id}")
        mock_logging.assert_called_once()

    @patch('src.audio_stream.views.logging.debug')
    def test_delete_rabbitmq_queue_handles_connection_closed_exception(self, mock_logging):
        # Arrange
        unique_id = "test-id"
        view_instance = AudioStreamView().__new__(AudioStreamView)
        view_instance.max_buffer_size = 15
        view_instance.queue_timeout = 5
        view_instance._rabbitmq_channel = MagicMock()
        view_instance._rabbitmq_channel.queue_delete.side_effect = ConnectionClosed(
            reply_text="test",
            reply_code=404
        )

        # Act
        view_instance.delete_rabbitmq_queue(unique_id)

        # Assert
        view_instance._rabbitmq_channel.queue_delete.assert_called_once_with(queue=f"audio_stream_{unique_id}")
        mock_logging.assert_called_once()
