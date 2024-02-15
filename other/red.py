"""
functions to print text in red to stdout
"""


def input_red(
        string: str = "ARE YOU SURE YOU WANT TO DUMP AND CREATE A NEW TABLE (YES/NO) "
) -> str:
    """
    @rtype: str
    @param string: the string to print in red
    @return: input from stdout
    """
    print("\033[91m", end="")
    user_input = input(string)
    print("\033[0m", end="")

    return user_input


def print_red(
        string: str = "RED"
) -> None:
    """
    @rtype: None
    @param string: string to print in red
    @return: Nothing
    """
    print("\033[91m", end="")
    print(string)
    print("\033[0m", end="")
