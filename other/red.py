

def inputRED(string: str = "ARE YOU SURE YOU WANT TO DUMP AND CREATE A NEW TABLE (YES/NO) ") -> str:
    print("\033[91m", end="")
    user_input = input(string)
    print("\033[0m", end="")

    return user_input


def printRED(string: str = "RED") -> None:
    print("\033[91m", end="")
    print(string)
    print("\033[0m", end="")

    return