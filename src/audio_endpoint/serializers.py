"""
This file contains the serializers for the API.
"""
from rest_framework import serializers

# pylint: disable=W0223
class MenuItemSerializer(serializers.Serializer):
    """
    This class is used to serialize the menu items.
    """
    item_name = serializers.CharField(
        max_length=100, default=""
    )
    quantity = serializers.ListField(
        child=serializers.IntegerField(), default=[]
    )
    price = serializers.ListField(child=serializers.DecimalField(
        max_digits=5, decimal_places=2), default=[]
    )
    temp = serializers.CharField(max_length=50, required=False, default="")
    add_ons = serializers.ListField(child=serializers.CharField(
        max_length=100), required=False, default=[]
    )
    milk_type = serializers.CharField(
        max_length=50, required=False, default=""
    )
    sweeteners = serializers.ListField(child=serializers.CharField(
        max_length=200), required=False, default=[]
    )
    num_calories = serializers.ListField(
        child=serializers.CharField(max_length=100), default=[]
    )
    cart_action = serializers.CharField(
        max_length=25, default=""
    )
    size = serializers.CharField(
        max_length=50, required=False, default=""
    )


class AudioResponseSerializer(serializers.Serializer):
    """
    This class is used to serialize the audio response.
    """
    file_path = serializers.CharField(max_length=200)
    unique_id = serializers.CharField(max_length=100)
    json_order = MenuItemSerializer(many=True)
