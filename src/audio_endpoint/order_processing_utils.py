"""
This module contains helper functions that are used for preprocessing and formatting order data
"""
from rest_framework.response import Response
from rest_framework import status


def formatted_deal(
        order: dict
) -> list[dict] | Response:
    """
    @rtype: list[dict] | Response
    @param order: order from deal cache
    @return: formatted deal to include all the attributes the frontend needs
    """
    item_types = ['CoffeeItem', 'BeverageItem', 'FoodItem', 'BakeryItem']
    common_attributes = {'size': 'regular', 'temp': 'regular', 'add_ons': [], 'sweeteners': []}

    for item_type in ['CoffeeItem', 'BeverageItem']:
        if item_type in order:
            order[item_type].update(common_attributes)
            if item_type == 'CoffeeItem':
                order[item_type]['milk_type'] = 'regular'

    if not any(item_type in order for item_type in item_types):
        return Response({'error': 'item_type not found'}, status=status.HTTP_400_BAD_REQUEST)

    return [order]



def remove_duplicate_deal(
        deal: dict, orders: list[str]
) -> None:
    """
    @rtype: None
    @param deal: deal from deal cache
    @param orders: looks through transcription and removes any orders that are in the deal
    @return: None because orders is modified in place
    """
    item_types = ['CoffeeItem', 'BeverageItem', 'FoodItem', 'BakeryItem']
    order_to_remove = None

    for item_type in item_types:
        if item_type in deal:
            item_name = deal[item_type]['item_name']
            for order in orders:
                if item_name in order:
                    order_to_remove = order
                    break

    if order_to_remove:
        orders.remove(order_to_remove)
