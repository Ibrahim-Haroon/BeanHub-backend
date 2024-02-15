"""
This file contains the model for the audio file.
"""
import uuid
from django.db import models


class AudioFile(models.Model):
    """
    This class is used to create the model for the audio file.
    """
    file_path = models.CharField(max_length=100)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False)
    json_order = models.JSONField()
