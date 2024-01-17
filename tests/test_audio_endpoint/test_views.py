import pytest
from mock import MagicMock
from rest_framework.test import APIClient
from src.audio_endpoint.views import AudioView  

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def view():
    return AudioView()

def test_post_without_file_path(api_client, view):
    response = api_client.post('/audio_endpoint/', {}) 
    assert response.status_code == 400
    assert response.json() == {'error': 'file_path not provided'}

def test_post_with_file_path(api_client, view):
    with MagicMock() as m:
        m.post('http://127.0.0.0.1', text='response')
        response = api_client.post('/audio_endpoint/', {'file_path': 'test.wav'})
        assert response.status_code == 200
        assert 'file_path' in response.json()
        assert 'unique_id' in response.json()
        assert 'json_order' in response.json()