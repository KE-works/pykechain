import os
from contextlib import contextmanager

import six
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

    UUID check is performed based on a regex pattern:
        `r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"`

    :return: True if there is a match, otherwise False
    :rtype: bool
    """
    if re.match(UUID_REGEX_PATTERN, str(value)):
        return True
    else:
        return False


@contextmanager
def temp_chdir(cwd=None):
    """
    Create and return a temporary directory which you can use as a context manager.

    When you are out of the context the temprorary disk gets erased.

    .. versionadded:: 2.3

    :param cwd: path to change working directory back to path when out of context
    :type cwd: basestring or None
    :return: in context a temporary directory

    Example
    -------

    >>> with temp_chdir() as temp_dir:
    >>>     # do things here
    >>>     print(temp_dir)  # etc etc
    ...
    >>> # when moving out of the context the temp_dir is destroyed
    >>> pass

    """
    if six.PY3:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tempwd:
            origin = cwd or os.getcwd()
            os.chdir(tempwd)

            try:
                yield tempwd if os.path.exists(tempwd) else ''
            finally:
                os.chdir(origin)
    else:
        from tempfile import mkdtemp
        tempwd = mkdtemp()
        origin = cwd or os.getcwd()
        os.chdir(tempwd)
        try:
            yield tempwd if os.path.exists(tempwd) else ''
        finally:
            os.chdir(origin)