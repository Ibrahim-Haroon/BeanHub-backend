import pytest
from django.apps import apps

@pytest.mark.django_db
def test_default_auto_field():
    config = apps.get_app_config('audio_endpoint')
    assert config.default_auto_field == 'django.db.models.BigAutoField'

@pytest.mark.django_db
def test_name():
    config = apps.get_app_config('audio_endpoint')
    assert config.name == 'src.audio_endpoint'
