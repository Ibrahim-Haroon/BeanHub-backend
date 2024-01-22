order = [{'BakeryItem': {'item_name': 'glazed donut',
                         'quantity': [1],
                         'price': [2.0],
                         'num_calories': ['(200,500)'],
                         'cart_action': 'insertion'}},
         {'CoffeeItem': {'item_name': 'black coffee',
                         'quantity': [1,
                                      1],
                         'price': [2.5,
                                   10.0,
                                   2.0,
                                   0.5],
                         'temp': 'regular',
                         'add_ons': ['pump of caramel',
                                     'whipped cream'],
                         'milk_type': 'cream',
                         'sweeteners': [],
                         'num_calories': ['(300,400)',
                                          '(60,120)',
                                          '(2,10)',
                                          '(50,50)'],
                         'size': 'regular',
                         'cart_action': 'insertion'}}]

order1 = [{'CoffeeItem': {'item_name': 'black coffee',
                          'quantity': [1],
                          'price': [2.0],
                          'temp': 'regular',
                          'add_ons': [],
                          'milk_type': 'regular',
                          'sweeteners': [],
                          'num_calories': ['(2,10)'],
                          'size': 'regular',
                          'cart_action': 'insertion'}}]


order2 = [{'CoffeeItem': {'item_name': 'black coffee',
                          'quantity': [],
                          'price': [2.0],
                          'temp': 'regular',
                          'add_ons': [],
                          'milk_type': 'regular',
                          'sweeteners': [],
                          'num_calories': ['(2,10)'],
                          'size': 'regular',
                          'cart_action': 'modification'}},
          {'BakeryItem': {'item_name': 'glazed donut',
                          'quantity': [1],
                          'price': [2.0],
                          'num_calories': ['(200,500)'],
                          'cart_action': 'insertion'}}]


def parse_coffee_or_beverage_item(item: dict, key: str) -> dict:
    i, res = 0, {}

    item_modification = item[key]['cart_action'] == "modification"
    item_quantity = item[key]['quantity'][0] if item[key]['quantity'] else 1
    res['item_name'] = [
        item[key]['item_name'],
        item_quantity if not item_modification else -
        item_quantity,
        (item[key]['price'][i] *
         float(item_quantity)) if i < len(
            item[key]['price']) else 0]
    i += 1
    res['size'] = item[key]['size']
    res['temp'] = item[key]['temp']

    res['add_ons'] = []
    for j in range(len(item[key]['add_ons'])):
        modification = item[key]['cart_action'] == "modification"
        quantity = item[key]['quantity'][i] if i < len(
            item[key]['quantity']) else 1
        res['add_ons'].append([item[key]['add_ons'][j],
                               quantity if not modification else -quantity,
                               (item[key]['price'][i] * quantity)
                               if i < len(item[key]['price']) else 0])
        i += 1

    res['milk_type'] = []
    if item[key]['milk_type']:
        modification = item[key]['cart_action'] == "modification"
        quantity = item[key]['quantity'][i] if i < len(
            item[key]['quantity']) else 1
        res['milk_type'].append([item[key]['milk_type'],
                                 quantity if not modification else -quantity,
                                 (item[key]['price'][i] * quantity)
                                 if i < len(item[key]['price']) else 0])
        i += 1

    res['sweeteners'] = []
    for j in range(len(item[key]['sweeteners'])):
        modification = item[key]['cart_action'] == "modification"
        quantity = item[key]['quantity'][i] if i < len(
            item[key]['quantity']) else 1
        res['sweeteners'].append([item[key]['sweeteners'][j],
                                  quantity if not modification else -quantity,
                                  (item[key]['price'][i] * quantity)
                                  if i < len(item[key]['price']) else 0])
        i += 1

    return res


def parse_bakery_or_food_item(item: dict, key: str) -> dict:
    modification = item[key]['cart_action'] == "modification"
    quantity = item[key]['quantity'][0] if item[key]['quantity'] else 1
    return {'item_name': [
        item[key]['item_name'],
        quantity if not modification else -quantity,
        (item[key]['price'][0] * quantity)
        if 0 < len(item[key]['price']) else 0
    ]
    }


def parser(order) -> None:
    for item in order:
        res = {}
        for key in item:
            if item[key]['cart_action'] == 'question':
                print('question')
                continue

            if key == 'CoffeeItem' or key == 'BeverageItem':
                res = parse_coffee_or_beverage_item(item, key)
            elif key == 'FoodItem' or key == 'BakeryItem':
                res = parse_bakery_or_food_item(item, key)
            else:
                print('error')

        print(res)


if __name__ == '__main__':
    parser(order)
