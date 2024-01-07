from rest_framework import serializers


class AudioResponseSerializer(serializers.Serializer):
    file_path = serializers.CharField()
    unique_id = serializers.CharField()
    json_order = serializers.JSONField()

