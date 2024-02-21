import pytest
from django.test import TestCase
from src.audio_stream.apps import AudioStreamConfig


@pytest.mark.skip(
    reason="ready method will always be initialized first making it impossible to mock connections"
)
class AudioStreamConfigTest(TestCase):
    def test_app_name_is_correct(
            self
    ) -> None:
        # Arrange

        # Act

        # Assert
        self.assertEqual(AudioStreamConfig.name, 'src.audio_stream')

    def test_default_auto_field_is_set_correctly(
            self
    ) -> None:
        # Arrange

        # Act

        # Assert
        self.assertEqual(AudioStreamConfig.default_auto_field, 'django.db.models.BigAutoField')