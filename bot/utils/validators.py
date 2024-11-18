

def get_integer_from_string(string: str) -> int | None:
    try:
        integer = int(string)
        return integer
    except ValueError:
        return None
        