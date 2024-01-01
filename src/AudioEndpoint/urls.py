from django.urls import path
from .views import AudioUploadView

urlpatterns = [
    path('', AudioUploadView.as_view(), name='audio-upload'),
]