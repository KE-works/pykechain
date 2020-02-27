import warnings
from datetime import datetime
from typing import Text, Optional, List, Iterable, Union, Any

from pykechain.enums import Enum
from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import is_uuid


def check_text(text: Optional[Text], key: Text) -> Optional[Text]:
    if text is not None:
        if not isinstance(text, str):
            raise IllegalArgumentError('`{}` should be a string, "{}" is not.'.format(key, text))
    return text


def check_list_of_text(list_of_text: Optional[Iterable[Text]], key: Text) -> Optional[List[Text]]:
    if list_of_text is not None:
        if not isinstance(list_of_text, (list, tuple, set)) or not all(isinstance(t, Text) for t in list_of_text):
            raise IllegalArgumentError(
                '`{}` should be a list, tuple or set of strings, "{}" is not.'.format(key, list_of_text))
        list_of_text = list(set(list_of_text))
    return list_of_text


def check_enum(value: Optional[Any], enum: type(Enum), key: Text) -> Optional[Any]:
    if value is not None:
        if value not in enum.values():
            raise IllegalArgumentError('`{}` must be an option from enum {}, "{}" is not.\nChoose from: {}'.format(
                key, enum.__class__.__name__, value, enum.values()))
    return value


def check_datetime(dt: Optional[datetime], key: Text) -> Optional[Text]:
    if dt is not None:
        if isinstance(dt, datetime):
            if not dt.tzinfo:
                warnings.warn("`{}` '{}' is naive and not timezone aware, use pytz.timezone info. "
                              "Date will be interpreted as UTC time.".format(key, dt.isoformat(sep=' ')))
            dt = dt.isoformat(sep='T')
        else:
            raise IllegalArgumentError('`{}` should be a datetime.datetime() object, "{}" is not.'.format(key, dt))
    return dt


def check_team(team: Optional[Union[Text, 'Team']], method: Optional[callable]) -> Optional[Text]:
    if team is not None:
        from pykechain.models import Team
        if isinstance(team, Team):
            team = team.id
        elif is_uuid(team):
            team = team
        elif isinstance(team, str) and method:
            team = method(team).id
        else:
            raise IllegalArgumentError("`team` should be provided as a `models.Team` object, UUID or name, "
                                       "was provided as a {}".format(type(team)))
    return team


def check_user(user: Optional[Union[Text, 'User']], method: callable) -> Optional['User']:
    if user is not None:
        from pykechain.models import User
        if isinstance(user, str):
            user = method(username=user)
        elif isinstance(user, int):
            user = method(pk=user)
        elif isinstance(user, User):
            pass
        else:
            raise IllegalArgumentError('`user` must be of type `User`, `username` or an id: "{}" is not.'.format(user))
    return user
