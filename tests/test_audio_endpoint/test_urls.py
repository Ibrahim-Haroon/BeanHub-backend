# audio_endpoint/tests/test_views.py
from django.test import RequestFactory
from django.urls import reverse
from src.audio_endpoint.views import AudioView

def test_audio_view():
    # Create a request and associate it with the AudioView
    request = RequestFactory().get(reverse('audio-view'))
    response = AudioView.as_view()(request)

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Add more assertions based on your view's behavior and expected output
    # For example, you might want to check if certain data is present in the response
