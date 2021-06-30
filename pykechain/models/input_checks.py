import warnings
from datetime import datetime
from typing import Text, Optional, List, Iterable, Any, Callable, Dict, Union

from pykechain.enums import Enum
from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import is_uuid, is_url, Empty, empty, parse_datetime

iter_types = (list, tuple, set)


def check_type(value: Optional[Any], cls: Any, key: Text) -> Optional[Any]:
    """Validate any input to be an instance a specific class.

    :param value: value to check against
    :param cls: check to see if the value is of type class
    :param key: key
    """
    if value is not None and value is not empty:
        if not isinstance(value, cls):
            if isinstance(cls, iter_types):
                types = ', '.join(c.__name__ for c in cls)
            else:
                types = cls.__name__
            raise IllegalArgumentError('`{}` should be of type {}, "{}" ({}) is not.'.format(
                key, types, value, type(value)))
    return value


def check_uuid(uuid: Optional[Text], key: Optional[Text] = 'pk') -> Optional[Text]:
    """Validate the UUID input to be a correct UUID."""
    if uuid is not None and uuid is not empty:
        if not is_uuid(uuid):
            raise IllegalArgumentError('`{}` must be a valid UUID, "{}" ({}) is not.'.format(key, uuid, type(uuid)))
    return uuid


def check_text(text: Optional[Text], key: Text) -> Optional[Text]:
    """Validate text input to be a string."""
    if text is not None and text is not empty:
        if not isinstance(text, str):
            raise IllegalArgumentError('`{}` should be a string, "{}" ({}) is not.'.format(key, text, type(text)))
    return text


def check_url(url: Optional[Text], key: Text = 'url') -> Optional[Text]:
    """Validate text input to be a valid format URL."""
    url = check_text(text=url, key=key)
    if url is not None and url is not empty:
        if not is_url(url):
            raise IllegalArgumentError('`{}` should be a valid URL, "{}" ({}) is not.'.format(key, url, type(url)))
    return url


def check_list_of_text(list_of_text: Optional[Iterable[Text]], key: Text, unique: bool = False) -> Optional[List[Text]]:
    """Validate iterable input to be a list/tuple/set of strings."""
    if list_of_text is not None and list_of_text is not empty:
        if not isinstance(list_of_text, iter_types) or not all(isinstance(t, Text) for t in list_of_text):
            raise IllegalArgumentError(
                '`{}` should be a list, tuple or set of strings, "{}" ({}) is not.'.format(key, list_of_text,
                                                                                           type(list_of_text)))
        if unique:
            list_of_text = [t for i, t in enumerate(list_of_text) if list_of_text.index(t) == i]
    return list_of_text


def check_list_of_dicts(list_of_dicts: Optional[Iterable[Dict]],
                        key: Text,
                        fields: Optional[List[Text]] = None,
                        ) -> Optional[List[Dict]]:
    """Validate iterable input to be a list/tuple/set of dicts, optionally checking for required field names."""
    if list_of_dicts is not None and list_of_dicts is not empty:
        if not isinstance(list_of_dicts, iter_types) or not all(isinstance(d, dict) for d in list_of_dicts):
            raise IllegalArgumentError(
                '`{}` should be a list, tuple or set of dicts, "{}" ({}) is not.'.format(key, list_of_dicts,
                                                                                         type(list_of_dicts))
            )
        if fields:
            assert isinstance(fields, list) and all(isinstance(f, str) for f in fields), \
                '`fields` must be a list of strings.'
            missing_fields = set()
            for dictionary in list_of_dicts:
                for field in fields:
                    if field not in dictionary:
                        missing_fields.add(field)
            if missing_fields:
                raise IllegalArgumentError('Not every dict contains the required fields: "{}"\n'
                                           'Missing fields: "{}"'.format('", "'.join(fields),
                                                                         '", "'.join(list(missing_fields))))
    return list_of_dicts


def check_enum(value: Optional[Any], enum: type(Enum), key: Text) -> Optional[Any]:
    """Validate input to be an option from an enum class."""
    if value is not None and value is not empty:
        if value not in enum.values():
            raise IllegalArgumentError('`{}` must be an option from enum {}, "{}" ({}) is not.\nChoose from: {}'.format(
                key, enum.__class__.__name__, value, type(value), enum.values()))
    return value


def check_datetime(dt: Optional[Union[datetime, Text]], key: Text) -> Optional[Text]:
    """Validate a datetime value to be a datetime and be timezone aware."""
    if dt is not None and dt is not empty:
        if isinstance(dt, str):
            dt = parse_datetime(dt)

        if isinstance(dt, datetime):
            if not dt.tzinfo:
                warnings.warn("`{}` '{}' is naive and not timezone aware, use pytz.timezone info. "
                              "Date will be interpreted as UTC time.".format(key, dt.isoformat(sep=' ')))
            dt = dt.isoformat(sep='T')
        else:
            raise IllegalArgumentError(
                '`{}` should be a correctly formatted string or a datetime.datetime() object, '
                '"{}" ({}) is not.'.format(key, dt, type(dt)))
    return dt


def check_base(obj: Optional[Any],
               cls: Optional[type(object)] = None,
               key: Optional[Text] = 'object',
               method: Optional[Callable] = None,
               ) -> Optional[Text]:
    """
    Validate whether the object provided as input is a Base (or subclass) instance and return its ID.

    When the obj is None, it returns None. Otherwise it will check if the object is a pykechain class and will
    extract the UUID from it.

    It will NOT check if the uuid (if a UUID is provided) is an actual class. It won't lookup the UUID in KE-chain
    and check that against the corresponding pykechain class.

    :param obj: Object that needs the checking.
    :param cls: (optional) See if the object is of a certain pykechain Class (subclass of Base)
    :param key: (optional) a key that may be provided to improve the legability of the provided Error
    :param method: (optional) a method that is used to convert the object into an instance that has the attribute 'id'.
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
                '`{}` must be an ID, UUID or `{}` object, "{}" ({}) is not.'.format(key, cls.__name__, obj, type(obj)))
    return obj


def check_user(obj: Optional[Any],
               cls: Optional[type(object)] = None,
               key: Optional[Text] = 'user',
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
                    '`{}` must be an ID or `{}` object, "{}" ({}) is not.'.format(key, cls.__name__, obj, type(obj)))
        elif method:
            obj = method(obj).id
        else:
            raise IllegalArgumentError(
                '`{}` must be an ID or `{}` object, "{}" ({}) is not.'.format(key, cls.__name__, obj, type(obj)))
    return obj


def check_list_of_base(
        objects: Optional[List[Any]],
        cls: Optional[type(object)] = None,
        key: Optional[Text] = 'objects',
        method: Optional[Callable] = None,
) -> Optional[List[Text]]:
    """Validate the iterable of objects provided as input are Base (or subclass) instances and return a list of IDs.

    :param objects: list of objects to check
    :param cls: (optional) class to check objects against
    :param key: (optional) key to check
    :param method: (optional) method used to check with
    :return: list of UUID's in Text.
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
                    key, cls.__name__, '", "'.join([str(n) for n in not_recognized]))
            )
    return ids


def check_empty(value: Optional[Any]):
    """Validate whether the value provided is of class `Empty`."""
    if isinstance(value, Empty):
        return True
    return False
