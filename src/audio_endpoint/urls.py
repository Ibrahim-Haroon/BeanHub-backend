from django.urls import path
from .views import AudioView

urlpatterns = [
    path('', AudioView.as_view(), name='audio-view'),
]
