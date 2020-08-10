import os
import re
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import TypeVar, Iterable, Callable, Optional, Text, Dict  # noqa: F401

import pytz
import six

T = TypeVar("T")

UUID_REGEX_PATTERN = (
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
EMAIL_REGEX_PATTERN = (
    r"^([-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+"
    r"(\.[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+)*|^\""
    r"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*\")"
    r"@(?:[a-zA-Z0-9\[\]](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9\[\]]{2,6}\.?$"
)


def find(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Optional[T]:
    """Return the first item in the iterable that matches the predicate function."""
    for i in iterable:
        if predicate(i):
            return i

    return None


def is_uuid(value: Text) -> bool:
    """
    Check if the string value is a proper UUID string.

    UUID check is performed based on a regex pattern:
        `r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"`

    :return: True if there is a match, otherwise False
    :rtype: bool
    """
    return bool(re.match(UUID_REGEX_PATTERN, str(value)))


def is_url(value: Text) -> bool:
    """
    Return whether or not given value is a valid URL.

    If the value is valid URL this function returns ``True``.

    This validator implementation is taken and augmented from https://github.com/kvesteri/validators/
    Copyright (c) 2013-2014 Konsta Vesterinen, It is Licenced with the MIT license.

    This validator is based on the wonderful `URL validator of dperini`_.

    .. _URL validator of dperini:
        https://gist.github.com/dperini/729294

    :param value: an alleged url
    :type value: Text
    :return: True if it is an URL, otherwise False
    :rtype: bool

    Examples
    --------
    >>> is_url('http://foobar.dk')
    True
    >>> is_url('ftp://foobar.dk')
    True
    >>> is_url('http://10.0.0.1')
    True
    >>> is_url('http://foobar.d')
    False

    """
    ip_middle_octet = r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
    ip_last_octet = r"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"

    regex = re.compile(  # noqa: W605
        r"^"
        # protocol identifier
        r"(?:(?:https?|ftp)://)"
        # user:pass authentication
        r"(?:[-a-z\u00a1-\uffff0-9._~%!$&'()*+,;=:]+"
        r"(?::[-a-z0-9._~%!$&'()*+,;=:]*)?@)?"
        r"(?:"
        r"(?P<private_ip>"
        # IP address exclusion
        # private & local networks
        r"(?:(?:10|127)" + ip_middle_octet + r"{2}" + ip_last_octet + r")|"
        r"(?:(?:169\.254|192\.168)" + ip_middle_octet + ip_last_octet + r")|"
        r"(?:172\.(?:1[6-9]|2\d|3[0-1])" + ip_middle_octet + ip_last_octet + r"))"
        r"|"
        # private & local hosts
        r"(?P<private_host>" r"(?:localhost))" r"|"
        # IP address dotted notation octets
        # excludes loopback network 0.0.0.0
        # excludes reserved space >= 224.0.0.0
        # excludes network & broadcast addresses
        # (first & last IP address of each class)
        r"(?P<public_ip>"
        r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
        r"" + ip_middle_octet + r"{2}"
        r"" + ip_last_octet + r")"
        r"|"
        # IPv6 RegEx from https://stackoverflow.com/a/17871737
        r"\[("
        # 1:2:3:4:5:6:7:8
        r"([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|"
        # 1::                              1:2:3:4:5:6:7::
        r"([0-9a-fA-F]{1,4}:){1,7}:|"
        # 1::8             1:2:3:4:5:6::8  1:2:3:4:5:6::8
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        # 1::7:8           1:2:3:4:5::7:8  1:2:3:4:5::8
        r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        # 1::6:7:8         1:2:3:4::6:7:8  1:2:3:4::8
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        # 1::5:6:7:8       1:2:3::5:6:7:8  1:2:3::8
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
        # 1::4:5:6:7:8     1:2::4:5:6:7:8  1:2::8
        r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
        # 1::3:4:5:6:7:8   1::3:4:5:6:7:8  1::8
        r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        # ::2:3:4:5:6:7:8  ::2:3:4:5:6:7:8 ::8       ::
        r":((:[0-9a-fA-F]{1,4}){1,7}|:)|"
        # fe80::7:8%eth0   fe80::7:8%1
        # (link-local IPv6 addresses with zone index)
        r"fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|"
        r"::(ffff(:0{1,4}){0,1}:){0,1}"
        r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
        # ::255.255.255.255   ::ffff:255.255.255.255  ::ffff:0:255.255.255.255
        # (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
        r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|"
        r"([0-9a-fA-F]{1,4}:){1,4}:"
        r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
        # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33
        # (IPv4-Embedded IPv6 Address)
        r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])" r")\]|"
        # host name
        r"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
        # domain name
        r"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
        # TLD identifier
        r"(?:\.(?:[a-z\u00a1-\uffff]{2,}))" r")"
        # port number
        r"(?::\d{2,5})?"
        # resource path
        u"(?:/[-a-z\u00a1-\uffff0-9._~%!$&'()*+,;=:@/]*)?"
        # query string
        r"(?:\?\S*)?"
        # fragment
        r"(?:#\S*)?" r"$",
        re.UNICODE | re.IGNORECASE,
    )
    return bool(regex.match(value))


def is_valid_email(value: Text) -> bool:
    """
    Return whether or not given value is a valid email address.

    If the value is valid email this function returns ``True``.
    The email will only be checked if it contains the right form, not if the email
    address exist. There are many and better ways to check if the email is valid, but
    in this case we check if the email has the form of `name@domain.tld`.

    :param value: an alleged email
    :type value: Text
    :return: True if it is an email, otherwise False
    :rtype: bool

    Examples
    --------
    >>> is_valid_email("valid_email-address@example.com")
    True
    >>> is_valid_email("invalid@email")
    False

    """
    if re.match(EMAIL_REGEX_PATTERN, str(value)):
        return True
    else:
        return False


@contextmanager
def temp_chdir(cwd: Optional[Text] = None):
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
                yield tempwd if os.path.exists(tempwd) else ""
            finally:
                os.chdir(origin)
    else:
        from tempfile import mkdtemp

        tempwd = mkdtemp()
        origin = cwd or os.getcwd()
        os.chdir(tempwd)
        try:
            yield tempwd if os.path.exists(tempwd) else ""
        finally:
            os.chdir(origin)


def parse_datetime(value: Optional[Text]) -> Optional[datetime]:
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
            offset = offset.total_seconds() // 60
        sign = "-" if offset < 0 else "+"
        hhmm = "%02d%02d" % divmod(abs(offset), 60)
        name = sign + hhmm
        return timezone(timedelta(minutes=offset), name)

    DATETIME_RE = re.compile(
        r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})"
        r"[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})"
        r"(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?"
        r"(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$"
    )

    match = DATETIME_RE.match(value)
    if match:
        kw = match.groupdict()
        if kw["microsecond"]:
            kw["microsecond"] = kw["microsecond"].ljust(6, "0")
        tzinfo = kw.pop("tzinfo")
        if tzinfo == "Z":
            tzinfo = pytz.UTC
        elif tzinfo is not None:
            offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
            offset = 60 * int(tzinfo[1:3]) + offset_mins
            if tzinfo[0] == "-":
                offset = -offset
            tzinfo = _get_fixed_timezone(offset)
        kw = {k: int(v) for k, v in six.iteritems(kw) if v is not None}
        kw["tzinfo"] = tzinfo
        return datetime(**kw)


#
# The following functions are inspired by: https://github.com/okunishinishi/python-stringcase
# License: MIT
#


def camelcase(string: Text) -> Text:
    """Convert string into camel case.

    Inspired by: https://github.com/okunishinishi/python-stringcase
    License: MIT

    :param string: String to convert.
    :returns: Camel case string.

    Examples
    --------
    >>> camelcase('foo_bar_baz')
    fooBarBaz
    >>> camelcase('FooBarBaz')
    fooBarBaz

    """
    string = re.sub(r"^[\-_\.]", "", str(string))
    if not string:
        return string
    return lowercase(string[0]) + re.sub(
        r"[\-_\.\s]([a-z])", lambda matched: uppercase(matched.group(1)), string[1:]
    )


def capitalcase(string: Text) -> Text:
    """Convert string into capital case.

    First letters will be uppercase.

    Inspired by: https://github.com/okunishinishi/python-stringcase
    License: MIT

    :param string: String to convert.
    :returns: Capital case string.

    Examples
    --------
    >>> capitalcase('foo_bar_baz')
    Foo_bar_baz
    >>> capitalcase('FooBarBaz')
    FooBarBaz

    """
    string = str(string)
    if not string:
        return string
    return uppercase(string[0]) + string[1:]


def lowercase(string: Text) -> Text:
    """Convert string into lower case.

    Inspired by: https://github.com/okunishinishi/python-stringcase
    License: MIT

    :param string: String to convert.
    :returns: lower case string.

    Examples
    --------
    >>> lowercase('foo_bar_baz')
    Foo_bar_baz
    >>> lowercase('FooBarBaz')
    foobarbaz

    """
    return str(string).lower()


def snakecase(string: Text) -> Text:
    """Convert string into snake case.

    Join punctuation with underscore

    Inspired by: https://github.com/okunishinishi/python-stringcase
    License: MIT


    :param string: String to convert.
    :returns: snake_case_string.


    Examples
    --------
    >>> snakecase('foo_bar_baz')
    foo_bar_baz
    >>> snakecase('FooBarBaz')
    foo_bar_baz

    """
    string = re.sub(r"[\-\.\s]", "_", str(string))
    if not string:
        return string
    return lowercase(string[0]) + re.sub(
        r"[A-Z]", lambda matched: "_" + lowercase(matched.group(0)), string[1:]
    )


def uppercase(string: Text) -> Text:
    """Convert string into upper case.

    Inspired by: https://github.com/okunishinishi/python-stringcase
    License: MIT

    :param string: String to convert.
    :returns: Upper case string.

    Examples
    --------
    >>> uppercase('foo_bar_baz')
    FOO_BAR_BAZ
    >>> uppercase('FooBarBaz')
    FOOBARBAZ

    """
    return str(string).upper()


def slugify_ref(value: Text, allow_unicode: bool = False) -> Text:
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.

    Remove characters that aren't alphanumerics, underscores, or hyphens. Convert to lowercase.
    Also strip leading and trailing whitespace.

    :param value: text to slugify
    :param allow_unicode: (optional) boolean to allow unicode processing, defaults to False
    :return: slugified value
    """
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
        value = re.sub(r"[^\w\s-]", "", value, flags=re.U).strip().lower()
        return re.sub(r"[-\s]+", "-", value, flags=re.U)
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def __dict_public__(cls: type(object)) -> Dict:
    """
    Get the __dict__ of the class `cls`, excluding 'dunder' attributes and methods.

    :param cls: class object
    :return: dictionary with public attributes

    Example
    -------
    >>> from pykechain.enums import Category
    >>> sorted(__dict_public__(cls=Category).values())
    ['INSTANCE', 'MODEL']

    """
    return {k: v for (k, v) in cls.__dict__.items() if not k.startswith("__")}


def __dict__inherited__(cls: type(object), stop: type(object) = type, public: Optional[bool] = True) -> Dict:
    """
    Get all __dict__ items of the class and its superclasses up to `type`, or the `stop` class given as input.

    :param cls: class from which to retrieve the dict.
    :type cls: type(object)
    :param stop: optional class to indicate up to which superclass the inheritance should accumulate the dict.
    :type stop: type(object)
    :param public: optional flag, will only retrieve public (without double underscore) attributes and methods.
    :type public: bool
    :return: dictionary of key, value pairs
    :rtype dict

    Example
    -------
    >>> from pykechain.enums import Enum, Category
    >>> sorted(__dict__inherited__(cls=Category, stop=Enum, public=True).values())
    ['INSTANCE', 'MODEL']

    """
    if public:
        _dict = __dict_public__(cls=cls)
    else:
        _dict = cls.__dict__

    for super_class in cls.mro():
        if super_class == stop:
            break
        if public:
            super_class_dict = __dict_public__(cls=super_class)
        else:
            super_class_dict = super_class.__dict__
        _dict.update(super_class_dict)

    return _dict
