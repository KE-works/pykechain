import warnings
from datetime import datetime
from typing import Text, Optional, List, Iterable, Union

from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import is_uuid


def _check_datetime(dt: Optional[datetime], key: Text) -> Optional[Text]:
    if dt is not None:
        if isinstance(dt, datetime):
            if not dt.tzinfo:
                warnings.warn("`{}` '{}' is naive and not timezone aware, use pytz.timezone info. "
                              "Date will be interpreted as UTC time.".format(key, dt.isoformat(sep=' ')))
            dt = dt.isoformat(sep='T')
        else:
            raise IllegalArgumentError('`{}` should be a datetime.datetime() object, "{}" is not.'.format(key, dt))
    return dt


def _check_tags(tags: Optional[Iterable[Text]]) -> Optional[List[Text]]:
    if tags is not None:
        if not isinstance(tags, (list, tuple, set)) or not all(isinstance(t, Text) for t in tags):
            raise IllegalArgumentError("`tags` should be a list, tuple or set of strings. "
                                       "Received type '{}'.".format(type(tags)))
        tags = list(set(tags))
    return tags


def _check_team(team: Optional[Union[Text, 'Team']], method: Optional[callable]) -> Optional[Text]:
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
