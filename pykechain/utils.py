import os
import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import TypeVar, Iterable, Callable, Optional, AnyStr  # noqa: F401

import six
import pytz

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


def parse_datetime(value):
    """
    Convert datetime string to datetime object.

    Helper function to convert a datetime string found in json responses to a datetime object with timezone information.
    The server is storing all datetime strings as UTC (ZULU time). This function supports time zone offsets. When
    the input contains one, the output uses a timezone with a fixed offset from UTC.

    Inspired on the Django project. From `django.utils.dateparse.parse_datetime`. The code is copyrighted and
    licences with an MIT license in the following fashion::

        Copyright (c) Django Software Foundation and individual contributors.
        All rights reserved.

    ..versionadded 2.5:

    :param value: datetime string
    :type value: str or None
    :return: datetime of the value is well formatted. Otherwise (including if value is None) returns None
    :rtype: datetime or None
    :raises ValueError: if the value is well formatted but not a valid datetime
    """
    if value is None:
        # do not process the value
        return None

    def _get_fixed_timezone(offset):
        """Return a tzinfo instance with a fixed offset from UTC."""
        if isinstance(offset, timedelta):
            offset = offset.seconds // 60
        sign = '-' if offset < 0 else '+'
        hhmm = '%02d%02d' % divmod(abs(offset), 60)
        name = sign + hhmm
        return pytz.FixedOffset(offset, name)

    DATETIME_RE = re.compile(
        r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
        r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
        r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
        r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$'
    )

    match = DATETIME_RE.match(value)
    if match:
        kw = match.groupdict()
        if kw['microsecond']:
            kw['microsecond'] = kw['microsecond'].ljust(6, '0')
        tzinfo = kw.pop('tzinfo')
        if tzinfo == 'Z':
            tzinfo = pytz.UTC
        elif tzinfo is not None:
            offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
            offset = 60 * int(tzinfo[1:3]) + offset_mins
            if tzinfo[0] == '-':
                offset = -offset
            tzinfo = _get_fixed_timezone(offset)
        kw = {k: int(v) for k, v in six.iteritems(kw) if v is not None}
        kw['tzinfo'] = tzinfo
        return datetime(**kw)
