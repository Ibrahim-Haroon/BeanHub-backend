import pytest
from typing import Final
from mock import MagicMock
from speech_recognition import WaitTimeoutError
from src.ai_integration.speech_to_text_api import google_cloud_speech_api, return_as_wav, record_until_silence

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


@pytest.fixture
def mock_microphone(mocker):
    return mocker.patch(script_path + '.speech.Microphone')


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


def test_return_as_wave_returns_byte_object(

) -> None:
    mock_audio_data = b'mock audio data'

    actual_return = return_as_wav(mock_audio_data)

    assert isinstance(actual_return, bytes), f"expected return to be bytes but got {type(actual_return)}"


def test_record_until_silence_returns_expected_audio_bytes_and_transcription(
        mock_google_cloud, mock_microphone
) -> None:
    # Arrange
    mock_recognizer_instance = MagicMock()
    mock_google_cloud.return_value = mock_recognizer_instance
    mock_microphone_instance = MagicMock()
    mock_microphone.return_value = mock_microphone_instance

    expected_audio_data = b''
    expected_transcribed_audio = None
    mock_recognizer_instance.recognize_google.return_value = expected_transcribed_audio

    mock_recognizer_instance.listen.side_effect = [
        WaitTimeoutError()
    ]

    # Act
    audio_data, transcribed_audio = record_until_silence()

    # Assert
    assert audio_data == expected_audio_data, f"Expected audio data to be {expected_audio_data}, but got {audio_data}"
    assert transcribed_audio == expected_transcribed_audio, f"Expected transcribed audio to be '{expected_transcribed_audio}', but got '{transcribed_audio}'"
