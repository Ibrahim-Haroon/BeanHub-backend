import os
import pytest
from typing import Final
from mock import MagicMock, patch
from speech_recognition import WaitTimeoutError
from src.ai_integration.speech_to_text_api import google_cloud_speech_api, return_as_wav, record_until_silence, nova_speech_api, save_as_mp3, whisper_speech_api, whisper_multi_speech_api

script_path: Final[str] = 'src.ai_integration.speech_to_text_api'


@pytest.fixture
def mock_google_cloud(
        mocker
) -> MagicMock:
    return mocker.patch(script_path + '.speech.Recognizer')


@pytest.fixture
def mock_deepgram(mocker):
    return mocker.patch(script_path + '.Deepgram')


@pytest.fixture
def mock_speech(
        mocker
) -> MagicMock:
    return mocker.patch(script_path + '.speech.AudioFile')


@pytest.fixture
def mock_microphone(mocker):
    return mocker.patch(script_path + '.speech.Microphone')


@pytest.fixture
def mock_audio_segment(mocker):
    return mocker.patch(script_path + '.AudioSegment')


@pytest.fixture
def mock_whisper(mocker):
    return mocker.patch(script_path + '.whisper')


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


def test_nova_speech_api_returns_expected_transcription_with_env_api_key(mocker, mock_deepgram):
    # Arrange
    mocker.patch(script_path + '.open', mocker.mock_open(read_data='foo'))
    mocker.patch.dict(os.environ, {
        "DEEPGRAM_API_KEY": "fake_env_api_key"
    })
    fake_response = {
        'results': {
            'channels': [
                {'alternatives': [{'transcript': 'test transcription'}]}
            ]
        }
    }
    mock_deepgram_instance = mocker.MagicMock()
    mock_deepgram_instance.transcription.sync_prerecorded.return_value = fake_response
    mock_deepgram.return_value = mock_deepgram_instance


    # Act
    transcript = nova_speech_api('test_audio.wav')


    # Assert
    assert transcript == 'test transcription', f"expected transcript to be 'test transcription' but got {transcript}"


def test_nova_speech_api_returns_expected_transcription_with_file_api_key(mocker, mock_deepgram):
    # Arrange
    mocker.patch(script_path + '.open', mocker.mock_open(read_data='fake_api_key'))
    fake_response = {
        'results': {
            'channels': [
                {'alternatives': [{'transcript': 'test transcription'}]}
            ]
        }
    }
    mock_deepgram_instance = mocker.MagicMock()
    mock_deepgram_instance.transcription.sync_prerecorded.return_value = fake_response
    mock_deepgram.return_value = mock_deepgram_instance

    # Act
    transcript = nova_speech_api('test_audio.wav')

    # Assert
    assert transcript == 'test transcription', f"expected transcript to be 'test transcription' but got {transcript}"


def test_save_as_mp3(mock_audio_segment, capsys):
    # Arrange
    mock_audio_data = b'mock audio data'
    output_filename = "test_audio.mp3"
    mock_audio_instance = MagicMock()
    mock_audio_segment.return_value = mock_audio_instance

    # Act
    save_as_mp3(mock_audio_data, output_filename, print_completion=True)
    captured = capsys.readouterr()

    # Assert
    mock_audio_segment.assert_called_with(mock_audio_data, sample_width=2, frame_rate=44100, channels=1)
    mock_audio_instance.export.assert_called_with(output_filename, format="wav")
    assert f"Audio saved as {output_filename}" in captured.out, "expected completion message in stdout but got nothing"


def test_save_as_mp3_prints_completion_message(mock_audio_segment, capsys):
    # Arrange
    mock_audio_data = b'mock audio data'
    output_filename = "test_audio.mp3"

    # Act
    save_as_mp3(mock_audio_data, output_filename=output_filename, print_completion=True)
    captured = capsys.readouterr()

    # Assert
    assert f"Audio saved as {output_filename}" in captured.out


def test_whisper_multi_speech_api_returns_correct_transcription(mock_whisper):
    # Arrange
    expected_transcription = 'test transcription'
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_whisper.load_audio.return_value = 'mock_audio'
    mock_whisper.pad_or_trim.return_value = 'padded_or_trimmed_audio'
    mock_mel_spectrogram = MagicMock()
    mock_mel_spectrogram.to.return_value = MagicMock()
    mock_whisper.log_mel_spectrogram.return_value = mock_mel_spectrogram
    mock_model.device = 'cpu'
    mock_model.detect_language.return_value = (None, {'en': 1.0})
    mock_result = MagicMock()
    mock_result.text = 'test transcription'
    mock_whisper.decode.return_value = mock_result
    audio_file_path = "test/file/path"

    # Act
    transcription = whisper_multi_speech_api(audio_file_path)

    # Assert
    assert transcription == expected_transcription, f"Expected {expected_transcription} but got {transcription}"


def test_whisper_speech_api_returns_correct_transcription(mock_whisper):
    # Arrange
    expected_transcription = 'test transcription'
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_model.transcribe.return_value = {'text': 'test transcription'}
    audio_file_path = "test/file/path"

    # Act
    transcription = whisper_speech_api(audio_file_path)

    # Assert
    assert transcription == expected_transcription, f"Expected {expected_transcription} but got {transcription}"
