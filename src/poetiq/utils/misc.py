from typing import Any, Iterable

POETIQ_LINK = "[poetiq](https://pypi.org/project/poetiq)"


def list_as_args(lst: Iterable[Any]) -> str:
    """
    Transform list into a list of command line arguments.

    Example:
    >>> list_as_args(["new", "--description", "awesome description"])
    'new --description "awesome description"'
    """

    def strize(element: Any) -> str:
        ret = str(element)
        if " " in ret:
            ret = f'"{ret}"'
        return ret

    return " ".join(strize(element) for element in lst)


def dict_as_args(dct: dict) -> str:
    return " ".join(f"{key}={value}" for key, value in dct.items())


def find_line(lines: list[str], line: str) -> int | None:
    """
    Find line among lines.

    Return index in list or null if not found.
    """
    for idx, l in enumerate(lines):
        if l.strip() == line.strip():
            return idx

    return None


def find_line_startswith(lines: list[str], startswith: str) -> str | None:
    """
    Find line that starts with or null if not found.
    """
    for l in lines:
        if l.lstrip().startswith(startswith):
            return l
    return None
