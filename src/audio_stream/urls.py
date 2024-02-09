from django.urls import path
from .views import AudioStreamView
from os import getenv as env
from dotenv import load_dotenv

load_dotenv()


urlpatterns = [
    path(env('APP_AUDIO_STREAM_URL', default=''), AudioStreamView.as_view(), name='audio-stream'),
]