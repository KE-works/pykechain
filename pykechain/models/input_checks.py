from __future__ import annotations

import warnings
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

import jsonschema

from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import (
    Empty,
    empty,
    is_url,
    is_uuid,
    parse_date,
    parse_datetime,
    parse_time,
)

iter_types = (list, tuple, set)


def check_type(value: Optional[Any], cls: Any, key: str) -> Optional[Any]:
    """Validate any input to be an instance a specific class.

    :param value: value to check against
    :param cls: check to see if the value is of type class
    :param key: name of the object to display in the error message
    """
    if value is not None and value is not empty:
        if not isinstance(value, cls):
            if isinstance(cls, iter_types):
                types = ", ".join(c.__name__ for c in cls)
            else:
                types = cls.__name__
            raise IllegalArgumentError(
                '`{}` should be of type {}, "{}" ({}) is not.'.format(
                    key, types, value, type(value)
                )
            )
    return value


def check_client(value: "Client") -> "Client":
    """Validate the input being a KE-chain Client.

    :param value: the client to test
    """
    from pykechain import Client

    return check_type(value, Client, "client")


def check_uuid(uuid: Optional[str], key: Optional[str] = "pk") -> Optional[str]:
    """Validate the UUID input to be a correct UUID."""
    if uuid is not None and uuid is not empty:
        if not is_uuid(uuid):
            raise IllegalArgumentError(
                f'`{key}` must be a valid UUID, "{uuid}" ({type(uuid)}) is not.'
            )
    return uuid


def check_text(text: Optional[str], key: str) -> Optional[str]:
    """Validate text input to be a string."""
    if text is not None and text is not empty:
        if not isinstance(text, str):
            raise IllegalArgumentError(
                f'`{key}` should be a string, "{text}" ({type(text)}) is not.'
            )
    return text


def check_url(url: Optional[str], key: str = "url") -> Optional[str]:
    """Validate text input to be a valid format URL."""
    url = check_text(text=url, key=key)
    if url is not None and url is not empty:
        if not is_url(url):
            raise IllegalArgumentError(
                f'`{key}` should be a valid URL, "{url}" ({type(url)}) is not.'
            )
    return url


def check_list_of_text(
    list_of_text: Optional[Iterable[str]], key: str, unique: bool = False
) -> Optional[List[str]]:
    """Validate iterable input to be a list/tuple/set of strings."""
    if list_of_text is not None and list_of_text is not empty:
        if not isinstance(list_of_text, iter_types) or not all(
            isinstance(t, str) for t in list_of_text
        ):
            raise IllegalArgumentError(
                '`{}` should be a list, tuple or set of strings, "{}" ({}) is not.'.format(
                    key, list_of_text, type(list_of_text)
                )
            )
        if unique:
            list_of_text = [
                t for i, t in enumerate(list_of_text) if list_of_text.index(t) == i
            ]
    return list_of_text


def check_list_of_dicts(
    list_of_dicts: Optional[Iterable[Dict]],
    key: str,
    fields: Optional[List[str]] = None,
) -> Optional[List[Dict]]:
    """
    Validate iterable input to be a list/tuple/set of dicts.

    Optionally checking for required field names.

    :param list_of_dicts: list of dicts
    :param key: name of the object to display in the error message
    :param fields: list of fields that are required in each dict
    :raises IllegalArgumentError: if the list_of_dicts does not conform
    :returns: the list of dicts
    """
    if list_of_dicts is not None and list_of_dicts is not empty:
        if not isinstance(list_of_dicts, iter_types) or not all(
            isinstance(d, dict) for d in list_of_dicts
        ):
            raise IllegalArgumentError(
                '`{}` should be a list, tuple or set of dicts, "{}" ({}) is not.'.format(
                    key, list_of_dicts, type(list_of_dicts)
                )
            )
        if fields:
            assert isinstance(fields, list) and all(
                isinstance(f, str) for f in fields
            ), "`fields` must be a list of strings."
            missing_fields = set()
            for dictionary in list_of_dicts:
                for field in fields:
                    if field not in dictionary:
                        missing_fields.add(field)
            if missing_fields:
                raise IllegalArgumentError(
                    'Not every dict contains the required fields: "{}"\n'
                    'Missing fields: "{}"'.format(
                        '", "'.join(fields), '", "'.join(list(missing_fields))
                    )
                )
    return list_of_dicts


def check_enum(value: Optional[Any], enum: type(Enum), key: str) -> Optional[Any]:
    """Validate input to be an option from an enum class."""
    if value is not None and value is not empty:
        if value not in enum.values():
            raise IllegalArgumentError(
                '`{}` must be an option from enum {}, "{}" ({}) is not.\n'
                "Choose from: {}".format(
                    key, enum.__class__.__name__, value, type(value), enum.values()
                )
            )
    return value


def check_datetime(dt: Optional[Union[datetime, str]], key: str) -> Optional[str]:
    """Validate a datetime value to be a datetime and be timezone aware."""
    if dt is None or dt is empty:
        return dt
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    if isinstance(dt, datetime):
        if not dt.tzinfo:
            warnings.warn(
                f"`{key}` `{dt.isoformat(sep=' ')}` is naive and not timezone aware, "
                f"use pytz.timezone info. Date will be interpreted as UTC time."
            )
        return dt.isoformat(sep="T")
    else:
        raise IllegalArgumentError(
            f"`{key}` should be a correctly formatted string or a datetime.datetime() object, "
            f'"{dt}" ({type(dt)}) is not.'
        )


def check_date(dt: Optional[Union[datetime, str]], key: str) -> Optional[str]:
    """Validate a date value to be a date."""
    if dt is None or dt is empty:
        return dt
    if isinstance(dt, str):
        dt = parse_date(dt)
    if isinstance(dt, date):
        return dt.strftime("%Y-%m-%d")
    else:
        raise IllegalArgumentError(
            f"`{key}` should be a correctly formatted string or a datetime.date() object, "
            f'"{dt}" ({type(dt)}) is not.'
        )


def check_time(dt: Optional[Union[datetime, str]], key: str) -> Optional[str]:
    """Validate a time value to be a time."""
    if dt is None or dt is empty:
        return dt
    if isinstance(dt, str):
        dt = parse_time(dt)
    if isinstance(dt, time):
        return dt.strftime("%H:%M:%S")
    else:
        raise IllegalArgumentError(
            f"`{key}` should be a correctly formatted string or a datetime.time() object, "
            f'"{dt}" ({type(dt)}) is not.'
        )


def check_base(
    obj: Optional[Any],
    cls: Optional[type(object)] = None,
    key: Optional[str] = "object",
    method: Optional[Callable] = None,
) -> Optional[str]:
    """
    Validate whether the object provided is instance of Base (or subclass) and return its ID.

    When the obj is None, it returns None. Otherwise it will check if the object is a pykechain
    class and will extract the UUID from it.

    It will NOT check if the uuid (if a UUID is provided) is an actual class. It won't lookup
    the UUID in KE-chain and check that against the corresponding pykechain class.

    :param obj: Object that needs the checking.
    :param cls: (optional) See if the object is of a certain pykechain Class (subclass of Base)
    :param key: (optional) a key that may be provided to improve the legability of the provided
        Error
    :param method: (optional) a method or function that is used to convert the object into an
        instance that has the attribute 'id'.
    :returns: None or UUID
    :raises IllegalArgumentError: When the object is not of type of the class or not a UUID.
    """
    if obj is not None and obj is not empty:
        if cls is None:
            from pykechain.models import Base

            cls = Base

        if isinstance(obj, cls):
            obj = obj.id
        elif isinstance(obj, str) and is_uuid(obj):
            pass
        elif isinstance(obj, str) and method:
            obj = method(obj).id
        else:
            raise IllegalArgumentError(
                f'`{key}` must be an ID, UUID or `{cls.__name__}` object, "{obj}" ({type(obj)}) is'
                " not."
            )
    return obj


def check_user(
    obj: Optional[Any],
    cls: Optional[type(object)] = None,
    key: Optional[str] = "user",
    method: Optional[Callable] = None,
) -> Optional[int]:
    """Provide same functionality as check_base(), although users dont use UUID but integers."""
    if obj is not None and obj is not empty:

        if cls is None:
            from pykechain.models import User

            cls = User

        if isinstance(obj, cls):
            obj = obj.id
        elif isinstance(obj, (int, str)):
            try:
                obj = int(obj)
            except ValueError:
                raise IllegalArgumentError(
                    f'`{key}` must be an ID or `{cls.__name__}` object, "{obj}" ({type(obj)}) is'
                    " not."
                )
        elif method:
            obj = method(obj).id
        else:
            raise IllegalArgumentError(
                f'`{key}` must be an ID or `{cls.__name__}` object, "{obj}" ({type(obj)}) is not.'
            )
    return obj


def check_list_of_base(
    objects: Optional[List[Any]],
    cls: Optional[type(object)] = None,
    key: Optional[str] = "objects",
    method: Optional[Callable] = None,
) -> Optional[List[str]]:
    """
    Validate the iterable of objects are instance of Base (or subclass) and return a list of IDs.

    :param objects: list of objects to check
    :param cls: (optional) class to check objects against
    :param key: (optional) key to check
    :param method: (optional) method or function used to extract the `id` of the
        object (defaults `id`)
    :returns: list of UUID's in Text.
    """
    ids = None
    if objects is not None and objects is not empty:
        check_type(objects, iter_types, key=key)

        if cls is None:
            from pykechain.models import Base

            cls = Base

        ids = []
        not_recognized = []
        for obj in objects:
            try:
                ids.append(check_base(obj=obj, cls=cls, method=method))
            except IllegalArgumentError:
                not_recognized.append(obj)

        if not_recognized:
            raise IllegalArgumentError(
                'All `{}` must be IDs, UUIDs or `{}` objects, "{}" is/are not.'.format(
                    key, cls.__name__, '", "'.join([str(n) for n in not_recognized])
                )
            )
    return ids


def check_json(
    value: Union[dict, list], schema: dict, key: Optional[str] = None
) -> bool:
    """
    Validate value against a jsonschema.

    :param value: a dictionary or list that is to be validated against a jsonschema
    :param schema: the jsonschema in a jsonschema format
    :param key: the key to name inside the exception
    :return: The value when passing, when not passing it raises a jsonschema.ValidationError
    :raise jsonschema.ValidationError: When the json is not conforming the jsonschame
    :raises jsonschema.SchemaError: When the schema is incorrect.
    """
    if not isinstance(value, (type(None), Empty)):
        jsonschema.validate(value, schema)
    return value


def check_empty(value: Optional[Any]):
    """Validate whether the value provided is of class `Empty`."""
    if isinstance(value, Empty):
        return True
    return False
