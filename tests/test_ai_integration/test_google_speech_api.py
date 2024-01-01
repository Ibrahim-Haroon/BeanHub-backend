from src.ai_integration.google_speech_api import record_until_silence
from os import path


def test_record_until_silence_with_empty_audio_file():
    # Arrange
    audio_file_path = path.join(path.dirname(path.realpath(__file__)), "empty_audio.wav")
    expected_transcription = None

    # Act
    _, actual_transcription = record_until_silence(audio_file_path)

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be None but got {actual_transcription}"



def test_record_until_silence_with_non_empty_audio_file():
    # Arrange
    audio_file_path = path.join(path.dirname(path.realpath(__file__)), "test_audio.wav")
    expected_transcription = "this is a test"

    # Act
    _, actual_transcription = record_until_silence(audio_file_path)

    # Assert
    assert expected_transcription == actual_transcription, f"expected transcription to be {expected_transcription} but {actual_transcription}"
