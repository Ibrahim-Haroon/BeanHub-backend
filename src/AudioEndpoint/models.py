from django.db import models


class AudioFile(models.Model):
    audio_name = models.CharField(max_length=180)
    description = models.TextField(max_length=180)
    file = models.FileField(upload_to='audios/')
    floating_point_number = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

