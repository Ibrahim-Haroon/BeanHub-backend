# audio_endpoint/tests/test_models.py
import pytest
from django.db.utils import IntegrityError
from src.audio_endpoint.models import AudioFile
import uuid


@pytest.mark.django_db
def test_create_audio_file():
    # Create an AudioFile instance
    audio_file = AudioFile(
        file_path="example_path",
        json_order={"key": "value"}
    )

    # Save the instance to the database
    audio_file.save()

    # Retrieve the instance from the database
    saved_audio_file = AudioFile.objects.get(id=audio_file.id)

    # Assert that the saved instance has the same attributes
    assert saved_audio_file.file_path == "example_path"
    assert saved_audio_file.json_order == {"key": "value"}

    # Assert that the UUID is a valid UUID
    assert uuid.UUID(str(saved_audio_file.unique_id), version=4)


@pytest.mark.django_db
def test_unique_id_default_value():
    # Create two AudioFile instances
    audio_file1 = AudioFile.objects.create(file_path="path1", json_order={"key": "value"})
    audio_file2 = AudioFile.objects.create(file_path="path2", json_order={"key": "value"})

    # Assert that the UUIDs are different
    assert audio_file1.unique_id != audio_file2.unique_id


@pytest.mark.django_db
def test_required_fields():
    # Attempt to create an AudioFile without providing required fields
    with pytest.raises(IntegrityError):
        AudioFile.objects.create()

