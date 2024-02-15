"""
This file is used to configure the app name for the audio_stream app.
"""
from django.apps import AppConfig


class AudioStreamConfig(AppConfig):
    """
    This class is used to configure the app name for the audio_stream app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.audio_stream"
