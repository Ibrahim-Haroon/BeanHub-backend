"""
This file is used to configure the app name for the audio_endpoint app.
"""
from django.apps import AppConfig


class AudioEndpointConfig(AppConfig):
    """
    This class is used to configure the app name for the audio_endpoint app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.audio_endpoint"
