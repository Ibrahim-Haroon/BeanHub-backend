"""
functions to print text in red to stdout
"""


def input_red(
        string: str = "ARE YOU SURE YOU WANT TO DUMP AND CREATE A NEW TABLE (YES/NO) "
) -> str:
    """
    This function just takes input from stdin and prints to stdout in red
    @param string: the string to print in red
    @rtype: str
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
    This function just prints to stdout in red
    @param string: string to print in red
    @rtype: None
    @return: Nothing
    """
    print("\033[91m", end="")
    print(string)
    print("\033[0m", end="")
