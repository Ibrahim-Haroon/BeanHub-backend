from rest_framework import serializers


class AudioResponseSerializer(serializers.Serializer):
    file = serializers.FileField()
    floating_point_number = serializers.FloatField()
