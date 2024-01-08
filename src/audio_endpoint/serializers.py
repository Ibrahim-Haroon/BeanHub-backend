from rest_framework import serializers


class MenuItemSerializer(serializers.Serializer):
    item_name = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    temp = serializers.CharField(max_length=50, required=False)
    add_ons = serializers.CharField(max_length=100, required=False)
    milk_type = serializers.CharField(max_length=50, required=False)
    sweeteners = serializers.CharField(max_length=200, required=False)
    num_calories = serializers.CharField(max_length=100)
    cart_action = serializers.CharField(max_length=25)


class NestedMenuItemSerializer(serializers.Serializer):
    MenuItem = MenuItemSerializer()


class AudioResponseSerializer(serializers.Serializer):
    file_path = serializers.CharField(max_length=200)
    unique_id = serializers.CharField(max_length=100)
    json_order = serializers.ListField(child=NestedMenuItemSerializer())

