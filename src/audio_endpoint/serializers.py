from rest_framework import serializers


class AudioResponseSerializer(serializers.Serializer):
    file = serializers.CharField()
    floating_point_number = serializers.FloatField()

