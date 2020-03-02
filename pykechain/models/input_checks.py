import warnings
from datetime import datetime
from typing import Text, Optional, List, Iterable, Any, Callable

from pykechain.enums import Enum
from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import is_uuid


def check_type(value: Optional[Any], cls: Any, key: Text) -> Optional[Any]:
    """Validate any input to be an instance a specific class."""
    if value is not None:
        if not isinstance(value, cls):
            if isinstance(cls, (list, tuple, set)):
                types = ', '.join(c.__name__ for c in cls)
            else:
                types = cls.__name__
            raise IllegalArgumentError('`{}` should be of type {}, "{}" ({}) is not.'.format(
                key, types, value, type(value)))
    return value


def check_uuid(uuid: Optional[Text], key: Optional[Text] = 'pk') -> Optional[Text]:
    """Validate the UUID input to be a correct UUID."""
    if uuid is not None:
        if not is_uuid(uuid):
            raise IllegalArgumentError('`{}` must be a valid UUID, "{}" ({}) is not.'.format(key, uuid, type(uuid)))
    return uuid


def check_text(text: Optional[Text], key: Text) -> Optional[Text]:
    """Validate text input to be a string."""
    if text is not None:
        if not isinstance(text, str):
            raise IllegalArgumentError('`{}` should be a string, "{}" ({}) is not.'.format(key, text, type(text)))
    return text


def check_list_of_text(list_of_text: Optional[Iterable[Text]], key: Text) -> Optional[List[Text]]:
    """Validate iterable input to be a list/tuple/set of strings."""
    if list_of_text is not None:
        if not isinstance(list_of_text, (list, tuple, set)) or not all(isinstance(t, Text) for t in list_of_text):
            raise IllegalArgumentError(
                '`{}` should be a list, tuple or set of strings, "{}" ({}) is not.'.format(key, list_of_text,
                                                                                           type(list_of_text)))
        list_of_text = list(set(list_of_text))
    return list_of_text


def check_enum(value: Optional[Any], enum: type(Enum), key: Text) -> Optional[Any]:
    """Validate input to be an option from an enum class."""
    if value is not None:
        if value not in enum.values():
            raise IllegalArgumentError('`{}` must be an option from enum {}, "{}" ({}) is not.\nChoose from: {}'.format(
                key, enum.__class__.__name__, value, type(value), enum.values()))
    return value


def check_datetime(dt: Optional[datetime], key: Text) -> Optional[Text]:
    """Validate a datetime value to be a datetime and be timezone aware."""
    if dt is not None:
        if isinstance(dt, datetime):
            if not dt.tzinfo:
                warnings.warn("`{}` '{}' is naive and not timezone aware, use pytz.timezone info. "
                              "Date will be interpreted as UTC time.".format(key, dt.isoformat(sep=' ')))
            dt = dt.isoformat(sep='T')
        else:
            raise IllegalArgumentError(
                '`{}` should be a datetime.datetime() object, "{}" ({}) is not.'.format(key, dt, type(dt)))
    return dt


def check_base(obj: Optional[Any],
               cls: Optional[type(object)] = None,
               key: Optional[Text] = 'object',
               method: Optional[Callable] = None,
               ) -> Optional[Text]:
    """Validate the object provided as input, return its ID."""
    if obj is not None:

        if cls is None:
            from pykechain.models import Base
            cls = Base

        if isinstance(obj, cls):
            obj = obj.id
        elif isinstance(obj, int):
            obj = str(obj)
        elif isinstance(obj, str) and is_uuid(obj):
            pass
        elif isinstance(obj, str) and method:
            obj = method(obj).id
        else:
            raise IllegalArgumentError(
                '`{}` must be an ID, UUID or `{}` object, "{}" ({}) is not.'.format(key, cls.__name__, obj, type(obj)))
    return obj


def check_list_of_base(
        objects: Optional[List[Any]],
        cls: Optional[type(object)] = None,
        key: Optional[Text] = 'objects',
        method: Optional[Callable] = None,
) -> Optional[List[Text]]:
    """Validate the iterable of objects provided as input, return a list of IDs."""
    ids = None
    if objects is not None:
        check_type(objects, list, 'users')

        if cls is None:
            from pykechain.models import Base
            cls = Base

        ids = []
        not_recognized = []
        for obj in objects:
            try:
                ids.append(check_base(obj=obj, cls=cls, key=key, method=method))
            except IllegalArgumentError:
                not_recognized.append(obj)

        if not_recognized:
            raise IllegalArgumentError(
                'All `{}` must be IDs, UUIDs or `{}` objects, "{}" are not.'.format(
                    key, cls.__name__, '", "'.join(not_recognized))
            )
    return ids
