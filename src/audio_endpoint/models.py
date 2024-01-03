from django.db import models


class AudioFile(models.Model):
    file = models.CharField(max_length=100)
    floating_point_number = models.FloatField(null=True, blank=True)

