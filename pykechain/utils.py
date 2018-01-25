from typing import TypeVar, Iterable, Callable, Optional, AnyStr  # flake8: noqa

import re

T = TypeVar('T')

UUID_REGEX_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


def find(iterable, predicate):
    # type: (Iterable[T], Callable[[T], bool]) -> Optional[T]
    """Return the first item in the iterable that matches the predicate function."""
    for i in iterable:
        if predicate(i):
            return i

    return None


def is_uuid(value):
    # type: (AnyStr) -> bool
    """Check if the string value is a proper UUID string.

    :return: True if there is a match, otherwise False
    :rtype: bool
    """
    if re.match(UUID_REGEX_PATTERN, str(value)):
        return True
    else:
        return False
