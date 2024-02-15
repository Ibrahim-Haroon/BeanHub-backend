"""
This file is used to define the URL patterns for the audio app.
"""
# pylint: disable=all
from django.urls import path
from .views import AudioView
from os import getenv as env
from dotenv import load_dotenv

load_dotenv()


urlpatterns = [
    path(env('APP_AUDIO_ENDPOINT_URL', default=''), AudioView.as_view(), name='audio-view'),
]