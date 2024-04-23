"""
regex patterns for splitting orders
"""
from typing import Final


SIZE_PATTERN: Final = r'\b(small|medium|large|extra large)\b'

FLAVOR_PATTERN: Final = (
    r'\b(?!pump of |pumps of )'
    r'(vanilla|caramel|cinnamon|pumpkin|espresso spice|peppermint|chocolate|white '
    r'raspberry|blueberry|strawberry|peach|mango|banana|coconut|almond|hazelnut)'
    r'(?!\s+(donut|muffin|doughnut)s?)\b'
)

TEMPERATURE_PATTERN: Final = (
    r'\b(hot|cold|iced|warm|room temp|extra hot)'
    r'(?!\s+(chocolate|cocoa|tea|' + FLAVOR_PATTERN + r')s?)\b'
)

SWEETENER_PATTERN: Final = (
    r'\b(sugar|honey|liquid cane sugar|sweet n low|equal|butter pecan|pink velvet|'
    r'sugar packet|splenda packet|splenda)s?\b'
)

QUANTITY_PATTERN: Final = (
    r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|'
    r'fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|couple|few|'
    r'dozen|a lot|a|an|bakers dozen|\d+)\b'
)

COFFEE_PATTERN: Final = (
    r'\b(coffee|black coffee|cappuccino|latte|americano|macchiato|'
    r'frappuccino|chai latte|espresso)s?(?<!shot of)\b'
)

BEVERAGE_PATTERN: Final = (
    r'\b(water|waters|tea|hot chocolate|hot cocoa|apple juice|orange juice|cranberry juice|'
    r'plain pancake|blueberry pancake|chocolate chip pancake|strawberry pancake|'
    r'mango smoothie|pineapple smoothie|pina colada smoothie|vanilla milkshake|'
    r'lemon tea|mango tea|jasmine|green tea|mint tea)s?\b'
)

FOOD_PATTERN: Final = (
    r'\b(egg and cheese croissant|egg and cheese|bacon egg and cheese|fruit|yogurt|'
    r'oatmeal|egg and cheese on croissant||hash brown|'
    r'grilled cheese|egg and cheese on english muffin|plain bagel|'
    r''
    r'everything bagel|sesame bagel|asiago bagel)s?\b'
)

BAKERY_PATTERN: Final = (
    r'\b(brownie|blueberry muffin|glazed donut|'
    r'strawberry donut|strawberry doughnut|chocolate donut|'
    r'chocolate doughnut|glazed doughnut|munchkin|'
    r'boston cream donut|boston cream|lemon cake|chocolate chip muffin)s?\b'
)

ADD_ONS_PATTERN: Final = (
    r'\b(shot of espresso|whipped cream|pump of caramel|pumps of caramel|pump of '
    r'vanilla|pumps of vanilla|pump of sugar|pumps of sugar|liquid sugar|pump of '
    r'butter pecan|pumps of butter pecan)s?\b'
)

MILK_PATTERN: Final = (
    r'\b(whole milk|two percent milk|one percent milk|skim milk|almond milk|oat milk|'
    r'soy milk|coconut milk|half and half|heavy cream|cream)s?\b'
)

COMMON_ALLERGIES_PATTERN: Final = (
    r'\b(peanut|tree nut|shellfish|fish|wheat|soy|egg|milk|gluten|dairy|'
    r'lactose|sesame|mustard|sulfate)s?\b'
)

SPLIT_EXCEPTION_PATTERN: Final = (
    r'(?:' + FLAVOR_PATTERN +
    '|' + MILK_PATTERN +
    '|' + ADD_ONS_PATTERN +
    '|' + TEMPERATURE_PATTERN +
    '|' + 'cheese' +
    '|' + SWEETENER_PATTERN + r')'
)

SPLIT_PATTERN: Final = (
    r'\b(plus|get|and|also)\b'
    r'(?!\s+(\w+\s+){0,1}(?:' + SPLIT_EXCEPTION_PATTERN + r'))'
    r'(?!\s+(?:' + TEMPERATURE_PATTERN + r'))'
)
