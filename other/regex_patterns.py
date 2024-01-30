size_pattern = r'\b(small|medium|large|extra large)\b'

coffee_pattern = (
    r'\b(coffee|black coffee|coffees|cappuccino|latte|americano|macchiato|'
    r'frappuccino|chai latte|espresso)(?<!shot of)\b'
)

quantity_pattern = (
    r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|'
    r'fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|couple|few|'
    r'dozen|a lot|a|an)\b'
)

temperature_pattern = r'\b(hot|cold|iced|warm|room temp|extra hot)\b'

sweetener_pattern = (
    r'\b(sugar|honey|liquid cane sugar|sweet n low|equal|butter pecan|pink velvet|'
    r'sugar packets|splenda packet|splenda packets|splenda|splendas)\b'
)

flavor_pattern = (
    r'\b(?!pump of |pumps of )'
    r'(vanilla|caramel|cinnamon|pumpkin|espresso spice|peppermint|chocolate|white '
    r'raspberry|blueberry|strawberry|peach|mango|banana|coconut|almond|hazelnut)\b'
)

beverage_pattern = (
    r'\b(water|waters|tea|hot chocolate|hot cocoa|apple juice|orange juice|cranberry juice|'
    r'mango smoothie|pineapple smoothie|pina colada smoothie|vanilla milkshake|'
    r'lemon tea|mango tea|jasmine|green tea|mint tea)\b'
)

food_pattern = (
    r'\b(egg and cheese croissant|egg and cheese|bacon egg and cheese|fruit|yogurt|'
    r'oatmeal|egg and cheese on croissant|hashbrown|hashbrowns|hash brown|hash '
    r'browns|grilled cheese|egg and cheese on english muffin|plain bagel|'
    r'everything bagel|sesame bagel|asiago bagel)\b'
)

bakery_pattern = (
    r'\b(brownie|blueberry muffin|blueberry muffins|glazed donut|glazed donuts|'
    r'strawberry donut|strawberry doughnut|strawberry donuts|strawberry doughnuts|chocolate donut|'
    r'chocolate doughnut|chocolate doughnuts|glazed doughnut|glazed doughnuts|munchkins|munchkin|'
    r'chocolate donuts|donut|boston cream donuts|boston cream|lemon cake|chocolate chip muffin)\b'
)

add_ons_pattern = (
    r'\b(shot of espresso|whipped cream|pump of caramel|pumps of caramel|pump of '
    r'vanilla|pumps of vanilla|pump of sugar|pumps of sugar|liquid sugar|pump of '
    r'butter pecan|pumps of butter pecan)\b'
)

milk_pattern = (
    r'\b(whole milk|two percent milk|one percent milk|skim milk|almond milk|oat milk|'
    r'soy milk|coconut milk|half and half|heavy cream|cream)\b'
)

common_allergies = (
    r'\b(peanuts|tree nuts|tree nut|shellfish|fish|wheat|soy|eggs|milk|gluten|dairy|'
    r'lactose|sesame|mustard|sulfates)\b'
)

split_exception_pattern = (
    r'(?:' + flavor_pattern +
    '|' + milk_pattern +
    '|' + add_ons_pattern +
    '|' + temperature_pattern +
    '|' + sweetener_pattern + r')'
)


split_pattern = (
    r'\b(plus|get|and|also)\b'
    r'(?!\s+(\w+\s+){0,2}(?:' + split_exception_pattern + r'))'
)
