import re
from other.number_map import number_map
from other.regex_patterns import (
    size_pattern, coffee_pattern, quantity_pattern, temperature_pattern, sweetener_pattern,
    flavor_pattern, beverage_pattern, food_pattern, bakery_pattern, add_ons_pattern,
    milk_pattern, common_allergies
)


def split_order(order: str) -> list[str]:
    split_pattern = (
            r'(' + size_pattern +
            '|' + coffee_pattern +
            '|' + quantity_pattern +
            '|' + temperature_pattern +
            '|' + 'cheese' +
            '|' + sweetener_pattern +
            '|' + flavor_pattern +
            '|' + beverage_pattern +
            '|' + food_pattern +
            '|' + bakery_pattern +
            '|' + add_ons_pattern +
            '|' + milk_pattern +
            '|' + common_allergies +
            '|' + sweetener_pattern + r')'
    )

    result = re.split(split_pattern, order)
    result = [s.strip() for s in result if s is not None and s.strip()]

    return list(set(result))


def correct_coffee_order_quantities(
        order_details: dict, original_order: str
) -> list[str]:
    updated_quantities = []
    order = split_order(original_order)

    item_set = (set(order_details['coffee']) |
                set(order_details['add_ons']) |
                set(order_details['sweeteners']) |
                set(order_details['milk_type']))

    for index, item in enumerate(order):
        if index == 0 and len(order) > 1:
            continue
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
    updated_quantities = []
    order = split_order(original_order)

    item_set = (set(order_details['beverage']) |
                set(order_details['add_ons']) |
                set(order_details['sweeteners']))

    for index, item in enumerate(order):
        if index == 0 and len(order) > 1:
            continue
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
    updated_quantities = []
    order = split_order(original_order)

    item_set = set(order_details['food'])

    for index, item in enumerate(order):
        if index == 0 and len(order) > 1:
            continue
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
    updated_quantities = []
    order = split_order(original_order)

    item_set = set(order_details['bakery'])

    for index, item in enumerate(order):
        if index == 0 and len(order) > 1:
            continue
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

