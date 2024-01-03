from django.db import models


class AudioFile(models.Model):
    file = models.FileField(upload_to='audios/')
    floating_point_number = models.FloatField(null=True, blank=True)

