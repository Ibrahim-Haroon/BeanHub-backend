"""
Simple function to map a number to a string, for example:
    "one" -> 1
"""


def number_map(
        num: str
) -> int:
    """
    @rtype: int
    @param num: string representation of a number
    @return: integer representation of the number
    """
    _number_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "couple": 2,
        "few": 3,
        "dozen": 12,
        "a lot": 6,
        "a": 1,
        "an": 1,
        "bakers dozen": 13
    }

    return _number_map.get(num, 0x7FFFFFFF)
