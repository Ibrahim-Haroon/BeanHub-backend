"""
This module contains functions that correct the quantities of items in an order. For example,
if customer orders "A black coffee with cream and sugar", the function will correct set quantity
of cream and sugar to 1 if the customer did not specify a quantity.
"""
import re
from other.number_map import number_map
from other.regex_patterns import (
    SIZE_PATTERN, COFFEE_PATTERN, QUANTITY_PATTERN, TEMPERATURE_PATTERN, SWEETENER_PATTERN,
    FLAVOR_PATTERN, BEVERAGE_PATTERN, FOOD_PATTERN, BAKERY_PATTERN, ADD_ONS_PATTERN,
    MILK_PATTERN, COMMON_ALLERGIES_PATTERN
)


def split_order(
        order: str
) -> list[str]:
    """
    This function splits the order into a list of items using the regex patterns defined
    @param order: human-readable order
    @rtype: list[str]
    @return: list of items in the order, split by the pattern
    """
    split_pattern = (
            r'(?:' + SIZE_PATTERN +
            '|' + COFFEE_PATTERN +
            '|' + QUANTITY_PATTERN +
            '|' + TEMPERATURE_PATTERN +
            '|' + 'cheese' +
            '|' + SWEETENER_PATTERN +
            '|' + FLAVOR_PATTERN +
            '|' + BEVERAGE_PATTERN +
            '|' + FOOD_PATTERN +
            '|' + BAKERY_PATTERN +
            '|' + ADD_ONS_PATTERN +
            '|' + MILK_PATTERN +
            '|' + COMMON_ALLERGIES_PATTERN +
            '|' + SWEETENER_PATTERN + r')'
    )

    result = re.split(split_pattern, order)
    result = [s.strip() for s in result if s is not None and s.strip()]

    return result


def correct_coffee_order_quantities(
        order_details: dict, original_order: str
) -> list[str]:
    """
    This function corrects the quantities of the coffee order for when the customer did not specify a quantity
    @param order_details: dictionary of the coffee order
    @param original_order: original order
    @rtype: list[str]
    @return: quantity of each item in the order even if the customer did not specify a quantity
    """
    updated_quantities = []
    order = split_order(original_order)

    item_set = (set(order_details['coffee']) |
                set(order_details['add_ons']) |
                set(order_details['sweeteners']) |
                set(order_details['milk_type']))

    for index, item in enumerate(order):
        quantity = order[index - 1] if index > 0 else order[index]
        if item in item_set:
            if (
                    quantity.isnumeric() or
                    number_map(quantity) != 0x7fffffff
            ):
                updated_quantities.append(quantity)

            else:
                updated_quantities.append('1')

    return updated_quantities


def correct_beverage_order_quantities(
        order_details: dict, original_order: str
) -> list[str]:
    """
    This function corrects the quantities of the beverage order for when the customer did not specify a quantity
    @param order_details: dictionary of the beverage order
    @param original_order: original order
    @rtype: list[str]
    @return: quantity of each item in the order even if the customer did not specify a quantity
    """
    updated_quantities = []
    order = split_order(original_order)

    item_set = (set(order_details['beverage']) |
                set(order_details['add_ons']) |
                set(order_details['sweeteners']))

    for index, item in enumerate(order):
        quantity = order[index - 1] if index > 0 else order[index]
        if item in item_set:
            if (
                    quantity.isnumeric() or
                    number_map(quantity) != 0x7fffffff
            ):
                updated_quantities.append(quantity)

            else:
                updated_quantities.append('1')

    return updated_quantities


def correct_food_order_quantities(
        order_details: dict, original_order: str
) -> list[str]:
    """
    This function corrects the quantities of the food order for when the customer did not specify a quantity
    @param order_details: dictionary of the food order
    @param original_order: original order
    @rtype: list[str]
    @return: quantity of each item in the order even if the customer did not specify a quantity
    """
    updated_quantities = []
    order = split_order(original_order)

    item_set = set(order_details['food'])

    for index, item in enumerate(order):
        quantity = order[index - 1] if index > 0 else order[index]
        if item in item_set:
            if (
                    quantity.isnumeric() or
                    number_map(quantity) != 0x7fffffff
            ):
                updated_quantities.append(quantity)

            else:
                updated_quantities.append('1')

    return updated_quantities


def correct_bakery_order_quantities(
        order_details: dict, original_order: str
) -> list[str]:
    """
    This function corrects the quantities of the bakery order for when the customer did not specify a quantity
    @param order_details: dictionary of the bakery order
    @param original_order: original order
    @rtype: list[str]
    @return: quantity of each item in the order even if the customer did not specify a quantity
    """
    updated_quantities = []
    order = split_order(original_order)

    item_set = set(order_details['bakery'])

    for index, item in enumerate(order):
        quantity = order[index - 1] if index > 0 else order[index]
        if item in item_set:
            if (
                    quantity.isnumeric() or
                    number_map(quantity) != 0x7fffffff
            ):
                updated_quantities.append(quantity)

            else:
                updated_quantities.append('1')

    return updated_quantities
