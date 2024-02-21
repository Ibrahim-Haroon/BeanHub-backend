import pytest
from django.test import TestCase
from src.audio_endpoint.apps import AudioEndpointConfig


@pytest.mark.skip(
    reason="ready method will always be initialized first making it impossible to mock connections"
)
class AudioEndpointConfigTest(TestCase):
    def test_app_name_is_correct(
            self
    ) -> None:
        # Arrange

        # Act

        # Assert
        self.assertEqual(AudioEndpointConfig.name, 'src.audio_endpoint')

    def test_default_auto_field_is_set_correctly(
            self
    ) -> None:
        # Arrange

        # Act

        # Assert
        self.assertEqual(AudioEndpointConfig.default_auto_field, 'django.db.models.BigAutoField')

