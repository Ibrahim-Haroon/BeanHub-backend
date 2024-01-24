from django.urls import path
from .views import AudioView
from os import getenv as env
from dotenv import load_dotenv

load_dotenv()


urlpatterns = [
    path(env('APP_AUDIO_ENDPOINT_URL'), AudioView.as_view(), name='audio-view'),
]