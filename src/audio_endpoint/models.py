from django.db import models
import uuid


class AudioFile(models.Model):
    file_path = models.CharField(max_length=100)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False)
    json_order = models.JSONField(default=list)

