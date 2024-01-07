import pytest
from os import path
from mock import MagicMock
from src.ai_integration.google_speech_api import get_transcription
from typing import Final


script_path: Final[str] = 'src.ai_integration.google_speech_api'


@pytest.fixture
def mock_google_cloud(mocker):
    return mocker.patch(script_path + '.speech.Recognizer')


def test_get_transcription_with_none_passed_for_audio_file_path():
    # Arrange
    audio_file_path = path.join(path.dirname(path.realpath(__file__)), "empty_audio.wav")
    expected_transcription = "None"

    # Act
    actual_transcription = get_transcription()

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be None but got {actual_transcription}"



def test_get_transcription_with_empty_audio_file(mock_google_cloud):
    # Arrange
    audio_file_path = path.join(path.dirname(path.realpath(__file__)), "empty_audio.wav")
    expected = MagicMock()
    mock_google_cloud.return_value = expected
    expected_transcription = "N"
    expected.recognize_google.side_effect = expected_transcription

    # Act
    actual_transcription = get_transcription(audio_file_path)

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be None but got {actual_transcription}"


def test_get_transcription_with_non_empty_audio_file(mock_google_cloud):
    # Arrange
    audio_file_path = path.join(path.dirname(path.realpath(__file__)), "test_audio.wav")
    expected = MagicMock()
    mock_google_cloud.return_value = expected
    expected_transcription = "t"
    expected.recognize_google.side_effect = expected_transcription

    # Act
    actual_transcription = get_transcription(audio_file_path)

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be {expected_transcription} but {actual_transcription}"

