import pytest
from os import path
from mock import MagicMock
from src.ai_integration.speech_to_text_api import google_cloud_speech_api
from typing import Final


script_path: Final[str] = 'src.ai_integration.speech_to_text_api'


@pytest.fixture
def mock_google_cloud(
        mocker
) -> MagicMock:
    return mocker.patch(script_path + '.speech.Recognizer')


@pytest.fixture
def mock_speech(
        mocker
) -> MagicMock:
    return mocker.patch(script_path + '.speech.AudioFile')


def test_get_transcription_with_none_passed_for_audio_file_path(
        mock_speech
) -> None:
    # Arrange
    expected_transcription = "None"

    # Act
    actual_transcription = google_cloud_speech_api()

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be None but got {actual_transcription}"



def test_get_transcription_with_empty_audio_file(
        mock_google_cloud, mock_speech
) -> None:
    # Arrange
    audio_file_path = "test/file/path"
    mock_recognizer_instance = MagicMock()
    mock_google_cloud.return_value = mock_recognizer_instance
    expected_transcription = "None"
    mock_recognizer_instance.recognize_google.return_value = expected_transcription

    # Act
    actual_transcription = google_cloud_speech_api(audio_file_path)

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be None but got {actual_transcription}"


def test_get_transcription_with_non_empty_audio_file(
        mock_google_cloud, mock_speech
) -> None:
    # Arrange
    audio_file_path = "test/file/path"
    mock_recognizer_instance = MagicMock()
    mock_google_cloud.return_value = mock_recognizer_instance
    expected_transcription = "this is a test"
    mock_recognizer_instance.recognize_google.return_value = expected_transcription

    # Act
    actual_transcription = google_cloud_speech_api(audio_file_path)

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be {expected_transcription} but {actual_transcription}"

