from rest_framework import serializers
from .models import AudioFile


class AudioResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = ['file_path', 'unique_id', 'json_order']
