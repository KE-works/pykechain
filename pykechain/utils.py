from typing import TypeVar, Iterable, Callable, Optional

T = TypeVar('T')


def find(iterable, predicate):
    # type: (Iterable[T], Callable[[T], bool]) -> Optional[T]
    """Return the first item in the iterable that matches the predicate function."""
    for i in iterable:
        if predicate(i):
            return i

    return None
