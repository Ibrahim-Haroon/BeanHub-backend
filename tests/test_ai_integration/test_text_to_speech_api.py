from src.ai_integration.text_to_speech_api import openai_text_to_speech_api
import pytest
from mock import MagicMock, patch
from typing import Final

script_path: Final[str] = 'src.ai_integration.text_to_speech_api'


@pytest.fixture
def mock_openai(
        mocker
) -> MagicMock:
    return mocker.patch(script_path + '.OpenAI')


def test_openai_text_to_speech_api(
        mock_openai
) -> None:
    # Arrange
    mock_audio = MagicMock()
    mock_audio.stream_to_file.return_value = None
    mock_openai.return_value.audio.speech.create.return_value = mock_audio

    # Act
    with patch(script_path + '.OpenAI', return_value=mock_openai.return_value):
        openai_text_to_speech_api(
            text="Test text",
            api_key="foo_key",
            audio_file_path="test_audio.mp3")

    # Assert
    mock_openai.return_value.audio.speech.create.assert_called_once_with(
        model="tts-1",
        voice="nova",
        input="Test text"
    )
    mock_audio.stream_to_file.assert_called_once_with("test_audio.mp3")
